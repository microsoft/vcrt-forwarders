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
pushd runtimes\win10-x64\native\release
for /r %%d in (*.dll) do xcopy /y "%%~d" "%~dp0\Unity\x64"
popd
copy /y "%~dp0\LICENSE" "%~dp0\Unity\LICENSE.md"
copy /y "%~dp0\CHANGELOG.md" "%~dp0\Unity\CHANGELOG.md"
copy /y "%~dp0\README.md" "%~dp0\Unity\Documentation~\README.md"
copy /y "%~dp0\LICENSE" "%~dp0\Unity\Documentation~\LICENSE"

where nuget.exe >nul 2>&1 || echo Couldn't find nuget.exe! && goto :eof
nuget pack vcrt-forwarders.nuspec

where npm.cmd >nul 2>&1 || echo Couldn't find npm.cmd! && goto :eof
pushd Unity
npm pack
popd

popd
