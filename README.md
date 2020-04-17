# VCRT Forwarders Preview

This project contains App-local DLLs that forward to runtime DLLs that are required to run Visual C++ applications and components. The runtime DLLs being forwarded to should already be installed on a given machine, this can be done using the Visual C++ [Redistributable Packages](https://support.microsoft.com/en-us/help/2977003/the-latest-supported-visual-c-downloads).

## NuGet Package

The NuGet package Microsoft.VCRTForwarders.140 can be found [here](https://aka.ms/vcrtfwdnuget).

Referencing the package will include the appropriate version of the forwarders on supported architectures based
on the CRT (debug / release) in use. For projects using custom debug configurations and referencing the component DLL
directly rather than via project (i.e C++ applications), the 'VCRTForwarders-IncludeDebugCRT' property can be set to 'true'
for that configuration to ensure inclusion of the debug CRT forwarders.

## Sample usage

You can find samples of C++ and C# apps using the forwarders [here](https://aka.ms/regfreewinrtsample).

## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.microsoft.com.

When you submit a pull request, a CLA-bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., label, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Reporting Security Issues
Security issues and bugs should be reported privately, via email, to the
Microsoft Security Response Center (MSRC) at <[secure@microsoft.com](mailto:secure@microsoft.com)>.
You should receive a response within 24 hours. If for some reason you do not, please follow up via
email to ensure we received your original message. Further information, including the
[MSRC PGP](https://technet.microsoft.com/en-us/security/dn606155) key, can be found in the
[Security TechCenter](https://technet.microsoft.com/en-us/security/default).

## License
Copyright (c) Microsoft Corporation. All rights reserved.

Licensed under the [MIT License](./LICENSE).