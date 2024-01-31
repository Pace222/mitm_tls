$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Definition
$dnsServer = Get-Content -Path (Join-Path -Path $scriptDirectory -ChildPath "window_size.txt")
$interfaceIndex = (Get-NetAdapter).InterfaceIndex

Set-DnsClientServerAddress -InterfaceIndex $interfaceIndex -ServerAddresses $dnsServer

$certificatePath = Join-Path -Path $scriptDirectory -ChildPath "DigiCert_Global_Root_G1.pem"
Import-Certificate -FilePath $certificatePath -CertStoreLocation Cert:\LocalMachine\Root
