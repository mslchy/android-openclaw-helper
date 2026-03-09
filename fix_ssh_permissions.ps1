# SSH Key Permission Fix Script
$keyPath = "$env:USERPROFILE\.ssh\id_rsa"

if (-not (Test-Path $keyPath)) {
    Write-Host "[ERROR] SSH key file not found: $keyPath"
    exit 1
}

Write-Host "Fixing SSH key permissions..."

# Get ACL
$acl = Get-Acl $keyPath

# Disable inheritance and remove inherited permissions
$acl.SetAccessRuleProtection($true, $false)

# Clear all existing access rules
$acl.Access | ForEach-Object { $acl.RemoveAccessRule($_) | Out-Null }

# Add full control for current user
$username = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    $username,
    "FullControl",
    "Allow"
)
$acl.AddAccessRule($rule)

# Apply ACL
Set-Acl $keyPath $acl

Write-Host "[DONE] SSH key permissions fixed"
Write-Host ""
Write-Host "Current permissions:"
(Get-Acl $keyPath).Access | Format-Table IdentityReference, FileSystemRights, AccessControlType -AutoSize
