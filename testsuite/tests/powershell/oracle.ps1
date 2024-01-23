
$result = select-string -Path "hello.adb" -Pattern 'pouet'

if ($result -eq $null) {
   exit 1
} else {
   exit 0
}
