$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Definition
$dnsServer = Get-Content -Path (Join-Path -Path $scriptDirectory -ChildPath "old_window_size.txt")
$thumbprint="642F01402DD64234431026199BF3C9CAECFB4239"
$interfaceIndex=(Get-NetAdapter).InterfaceIndex[0]

Set-DnsClientServerAddress -InterfaceIndex $interfaceIndex -ServerAddresses $dnsServer

Get-ChildItem -Path Cert:\LocalMachine\Root | Where-Object { $_.Thumbprint -eq $thumbprint } | Remove-Item
