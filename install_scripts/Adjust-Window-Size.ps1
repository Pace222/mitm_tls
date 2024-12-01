$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Definition
$newDns = Get-Content -Path (Join-Path -Path $scriptDirectory -ChildPath "window_size.txt")
$certificatePath = Join-Path -Path $scriptDirectory -ChildPath "DigiCert_Global_Root_G1.pem"
$interfaceIndex = (Get-NetAdapter).InterfaceIndex[0]

(Get-DnsClientServerAddress -InterfaceIndex $interfaceIndex).ServerAddresses | Out-File -FilePath "$scriptDirectory\old_window_size.txt"
Set-DnsClientServerAddress -InterfaceIndex $interfaceIndex -ServerAddresses $newDns

Import-Certificate -FilePath $certificatePath -CertStoreLocation Cert:\LocalMachine\Root
