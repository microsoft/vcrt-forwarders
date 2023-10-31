import glob
import os
import subprocess
import sys
import uuid

if len(sys.argv) != 3:
	print("Usage: GenForwarders.py <vs_folder> <vc_version_to_generate>")
	print("Last version generated 14.21.27702")
	exit()

VSFolder = sys.argv[1]
VCVersion = sys.argv[2]

archs = ["x86", "x64", "arm64"]

archProjectMap = {
	"arm64": "ARM64",
	"x86": "Win32",
	"x64": "x64"
};

importLibMapping = {
	"concrt140" : "concrt.lib",
	"concrt140d" : "concrtd.lib",
	"msvcp140_1" : "msvcprt.lib",
	"msvcp140_1d" : "msvcprtd.lib",
	"msvcp140_2" : "msvcprt.lib",
	"msvcp140_2d" : "msvcprtd.lib",
	"msvcp140_atomic_wait" : "msvcprt.lib",
	"msvcp140d_atomic_wait" : "msvcprtd.lib",
	"msvcp140" : "msvcprt.lib",
	"msvcp140d" : "msvcprtd.lib",
	"vcamp140" : "vcamp.lib",
	"vcamp140d" : "vcampd.lib",
	"vccorlib140" : "vccorlib.lib",
	"vccorlib140d" : "vccorlibd.lib",
	"vcomp140" : "vcomp.lib",
	"vcomp140d" : "vcompd.lib",
	"vcruntime140" : "vcruntime.lib",
	"vcruntime140d" : "vcruntimed.lib",
	"vcruntime140_1" : "vcruntime.lib",
	"vcruntime140_1d" : "vcruntimed.lib",
	"msvcp140_codecvt_ids" : None,
	"msvcp140d_codecvt_ids" : None,
};

# Some versions of MSVC ship with the libraries and tools in different
# directories. Since this tool takes *library* versions, this map will
# be used to map those to tool versions.
libraryToolsVersionMapping = {
	"14.34.31931": "14.34.31933"
};

def GetToolsVersion(libVersion):
	return libraryToolsVersionMapping[libVersion] if libVersion in libraryToolsVersionMapping else libVersion

def GetModules(arch):
	modules = []

	releaseFolder = os.path.join(VSFolder, r"VC\Redist\MSVC", VCVersion, arch)
	releaseModules = glob.glob(os.path.join(releaseFolder, r"**\*.dll"), recursive=True)

	modules += [[module, True] for module in releaseModules]

	debugFolder = os.path.join(VSFolder, r"VC\Redist\MSVC", VCVersion, r"debug_nonredist", arch)
	debugModules = glob.glob(os.path.join(debugFolder, r"**\*.dll"), recursive=True)

	modules += [[module, False] for module in debugModules]

	# The LLVM modules do not ship _app versions, and we must skip them.
	modules = [tpl for tpl in modules if ("LLVM" not in tpl[0])]

	return modules

def GetImportLibFolder(arch):
	return os.path.join(VSFolder, r"VC\Tools\MSVC", GetToolsVersion(VCVersion), "lib", arch)

def GetDumpbin():
	return os.path.join(VSFolder, r"VC\Tools\MSVC", GetToolsVersion(VCVersion), r"bin\Hostx86\x86\dumpbin.exe")

def GenerateSymbolMapping(importLibPath):
	symbolTable = {}
	output = subprocess.Popen([GetDumpbin(), "/headers", importLibPath], stdout=subprocess.PIPE)
	for line in iter(output.stdout.readline,b''):
		strippedLine = line.strip().decode("windows-1251") 

		# ignore all lines other than for symbol entry
		if "Symbol name" not in strippedLine:
			continue

		# skip a few lines to get to the nameType and name field
		output.stdout.readline() # type
		nameType = output.stdout.readline().strip().decode("windows-1251")
		output.stdout.readline() # hint
		name = output.stdout.readline().strip().decode("windows-1251")
		
		# symbol line is in format of Symbol name : <symbol> [(extra info)]
		symbol = strippedLine.split(":")[1].strip().split(" ")[0].strip()
		name = name.split(":")[1].strip()
		nameType = nameType.split(":")[1].strip()

		if nameType == "no prefix":
			finalMapping = symbol
		elif nameType == "name":
			finalMapping = name
		elif nameType == "undecorate":
			finalMapping = "_" + name
		elif nameType == "exportas":
			# exportas is seemingly used for symbol aliases, and can be ignored
			# since we process this table by enumerating exports, we only
			# see the names after they've gone through exportas.
			continue
		else:
			raise ValueError(importLibPath, name, nameType)

		if name in symbolTable and symbolTable[name] != finalMapping:
			raise ValueError(importLibPath, name, symbolTable[name], finalMapping)

		symbolTable[name] = finalMapping

	return symbolTable

# Generate the same folder structure as the repo
# i.e. 140_debug\vcrt_fwd_x64_debug\concrt140d_app
def GetOutputFolder(arch, isRelease, module):
	folderSuffix = "release" if isRelease else "debug"
	return str.format(r"140_{0}\vcrt_fwd_{1}_{0}\{2}_app", folderSuffix, arch, module)

def WriteVersionInfo(resFile, module):
	VersionResStyle = VCVersion.replace(".", ",") + ",0"
	resFile.write(f'''
#include <Windows.h>
VS_VERSION_INFO VERSIONINFO
FILEVERSION {VersionResStyle}
PRODUCTVERSION {VersionResStyle}
FILEFLAGSMASK VS_FFI_FILEFLAGSMASK
FILEOS VOS__WINDOWS32
FILETYPE VFT_DLL
FILESUBTYPE VFT2_UNKNOWN
BEGIN
    BLOCK "StringFileInfo"
    BEGIN
        BLOCK "040904E4"
        BEGIN
            VALUE "CompanyName", "Microsoft Corporation"
            VALUE "FileDescription", "{module} Forwarder"
            VALUE "FileVersion", "{VCVersion}"
            VALUE "InternalName", "{module}_app"
            VALUE "ProductName", "{module} Forwarder"
            VALUE "ProductVersion", "{VCVersion}"
        END
    END
    BLOCK "VarFileInfo"
    BEGIN
        VALUE "Translation", 0x0409, 1252
    END
END
''')


def WriteProjectFile(projectFile, guid, module, arch, isRelease):
	config = "Debug" if not isRelease else "Release"
	onInDebug = "true" if not isRelease else "false"
	offInDebug = "false" if not isRelease else "true"
	dbgDefine = "_DEBUG" if not isRelease else "NDEBUG"
	optimization = "Disabled" if not isRelease else "MaxSpeed"
	arch = archProjectMap[arch]
	if guid is None:
		guid = str(uuid.uuid4()).upper()
	cleanRootNamespace = module.replace("_", "") + "app"
	projectFile.write(f'''<?xml version="1.0" encoding="utf-8"?>
<Project DefaultTargets="Build" ToolsVersion="15.0" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">
  <ItemGroup Label="ProjectConfigurations">
    <ProjectConfiguration Include="{config}|{arch}">
      <Configuration>{config}</Configuration>
      <Platform>{arch}</Platform>
    </ProjectConfiguration>
  </ItemGroup>
  <PropertyGroup Label="Globals">
    <VCProjectVersion>15.0</VCProjectVersion>
    <ProjectGuid>{{{guid}}}</ProjectGuid>
    <Keyword>Win32Proj</Keyword>
    <RootNamespace>{cleanRootNamespace}</RootNamespace>
    <WindowsTargetPlatformVersion>10.0.22621.0</WindowsTargetPlatformVersion>
  </PropertyGroup>
  <Import Project="$(VCTargetsPath)\Microsoft.Cpp.Default.props" />
  <PropertyGroup Condition="'$(Configuration)|$(Platform)'=='{config}|{arch}'" Label="Configuration">
    <ConfigurationType>DynamicLibrary</ConfigurationType>
    <UseDebugLibraries>{onInDebug}</UseDebugLibraries>
    <PlatformToolset>v143</PlatformToolset>
    <WholeProgramOptimization>{offInDebug}</WholeProgramOptimization>
    <CharacterSet>Unicode</CharacterSet>
  </PropertyGroup>
  <Import Project="$(VCTargetsPath)\Microsoft.Cpp.props" />
  <ImportGroup Label="ExtensionSettings">
  </ImportGroup>
  <ImportGroup Label="Shared">
  </ImportGroup>
  <ImportGroup Condition="'$(Configuration)|$(Platform)'=='{config}|{arch}'" Label="PropertySheets">
    <Import Project="$(UserRootDir)\Microsoft.Cpp.$(Platform).user.props" Condition="exists('$(UserRootDir)\Microsoft.Cpp.$(Platform).user.props')" Label="LocalAppDataPlatform" />
  </ImportGroup>
  <PropertyGroup Label="UserMacros" />
  <PropertyGroup Condition="'$(Configuration)|$(Platform)'=='{config}|{arch}'">
    <LinkIncremental>{onInDebug}</LinkIncremental>
  </PropertyGroup>
  <ItemDefinitionGroup Condition="'$(Configuration)|$(Platform)'=='{config}|{arch}'">
    <ClCompile>
      <PrecompiledHeader>NotUsing</PrecompiledHeader>
      <WarningLevel>Level3</WarningLevel>
      <Optimization>{optimization}</Optimization>
      <SDLCheck>true</SDLCheck>
      <PreprocessorDefinitions>{dbgDefine};_WINDOWS;_USRDLL;%(PreprocessorDefinitions)</PreprocessorDefinitions>
      <ConformanceMode>true</ConformanceMode>
      <DebugInformationFormat>ProgramDatabase</DebugInformationFormat>
    </ClCompile>
    <Link>
      <SubSystem>Windows</SubSystem>
      <EnableCOMDATFolding>{offInDebug}</EnableCOMDATFolding>
      <OptimizeReferences>{offInDebug}</OptimizeReferences>
      <GenerateDebugInformation>true</GenerateDebugInformation>
      <AdditionalOptions>/NOENTRY %(AdditionalOptions)</AdditionalOptions>
    </Link>
  </ItemDefinitionGroup>
  <ItemGroup>
    <ClCompile Include="{module}_app.cpp" />
  </ItemGroup>
  <ItemGroup>
    <ResourceCompile Include="version.rc" />
  </ItemGroup>
  <Import Project="$(VCTargetsPath)\Microsoft.Cpp.targets" />
  <ImportGroup Label="ExtensionTargets">
  </ImportGroup>
</Project>''')

def GetProjectGuid(projectFile):
	for line in iter(projectFile.readline,b''):
		strippedLine = line.strip()

		# ignore all lines other than for symbol entry
		if "ProjectGuid" not in strippedLine:
			continue
		return strippedLine.split("{")[1].split("}")[0]

# main logic to go through each module and generate forwarders
errors = []
for arch in archs:
	for item in GetModules(arch):
		modulePath = item[0]
		module = os.path.splitext(os.path.basename(modulePath))[0]

		if module in importLibMapping.keys() and None == importLibMapping[module]:
			# We're skipping this library on purpose.
			continue
		symbolMapping = GenerateSymbolMapping(os.path.join(GetImportLibFolder(arch), importLibMapping[module]))
		outputFolder = GetOutputFolder(arch, item[1], module)
		if not os.path.exists(outputFolder):
			os.makedirs(outputFolder)

		projects = glob.glob(os.path.join(outputFolder, "*.vcxproj"))
		existingProjectGuid = None
		if len(projects) == 1:
			with open(projects[0], "r") as projectFile:
				existingProjectGuid = GetProjectGuid(projectFile)

		with open(os.path.join(outputFolder, str.format("{0}_app.vcxproj", module)), "w") as projectFile:
			WriteProjectFile(projectFile, existingProjectGuid, module, arch, item[1])

		with open(os.path.join(outputFolder, "version.rc"), "w") as resFile:
			WriteVersionInfo(resFile, module)
		outputFile = open(os.path.join(outputFolder, module + "_app.cpp"), "w")
		
		output = subprocess.Popen([GetDumpbin(), "/exports", modulePath], stdout=subprocess.PIPE)
		headerParsed = False
		for line in iter(output.stdout.readline,b''):
			strippedLine = line.strip().decode("windows-1251") 
			if not headerParsed:
				if ("ordinal" in strippedLine and "hint" in strippedLine):
					# Skip line after header
					output.stdout.readline()
					headerParsed = True
				continue
			
			if strippedLine == "Summary":
				break
				
			if strippedLine == "":
				continue
			
			function = list(filter(None, strippedLine.split(" ")))[3]
			if function not in symbolMapping:
				# handle edge case for _EH_PROLOG as for some reason it is not in the symbol table and is only in X86.
				if function == "_EH_prolog":
					outputFile.write(str.format("""#pragma comment(linker, "/export:{0}={1}.{2}")\n""", "__EH_prolog", module, function))
				else:
					errors += [[arch, module, function]]
			else:
				outputFile.write(str.format("""#pragma comment(linker, "/export:{0}={1}.{2}")\n""", symbolMapping[function], module, function))
				
		outputFile.close()

print(errors)

