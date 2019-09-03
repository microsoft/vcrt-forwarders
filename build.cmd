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

where nuget.exe >nul 2>&1 || echo Couldn't find nuget.exe! && goto :eof
nuget pack vcrt-forwarders.nuspec

popd
