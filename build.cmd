@echo off
pushd %~dp0

for %%c in (debug release) do (
	for %%p in (x86 x64 arm64) do (
		pushd 140_%%c\vcrt_fwd_%%p_%%c
		msbuild
		for /r %%d in (*.dll) do xcopy /y "%%~d" "%~dp0\runtimes\win10-%%p\native\%%c\"
		popd
	)
)

@rem Prepare for UPM packaging
for /r %%d in (140_release\vcrt_fwd_x64_release\*.dll) do xcopy /y "%%~d" "%~dp0\Unity\x64"
for %%f in (LICENSE CHANGELOG.md README.md) do copy /y "%~dp0\%%f" "%~dp0\Unity\%%f"

where nuget.exe >nul 2>&1 || echo Couldn't find nuget.exe! && goto :eof
nuget pack vcrt-forwarders.nuspec

where npm.cmd >nul 2>&1 || echo Couldn't find npm.cmd! && goto :eof
pushd Unity
npm pack
popd

popd
