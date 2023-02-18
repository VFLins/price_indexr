# Coletar dados
Set-Location $PSScriptRoot
Set-Location ..
$DB_ID = 'radeon_rx_6600_xt'

Write-Output "Coletando preços da POWERCOLOR RX 6600 XT FIGHTER..."
./pyenv/Scripts/python.exe price_indexr.py $DB_ID "POWERCOLOR RX 6600 XT FIGHTER -rig -minera -Notebook -PC -xiaomi -cooler"

Write-Output "Coletando preços da MSI RX 6600 XT GAMING X..."
./pyenv/Scripts/python.exe price_indexr.py $DB_ID "MSI RX 6600 XT GAMING X -rig -minera -Notebook -PC -xiaomi -cooler"

Write-Output "Coletando preços da SAPPHIRE RX 6600 XT NITRO+..."
./pyenv/Scripts/python.exe price_indexr.py $DB_ID "SAPPHIRE RX 6600 XT NITRO -rig -minera -Notebook -PC -xiaomi -cooler"

Write-Output "Coletando preços da SAPPHIRE RX 6600 XT PULSE..."
./pyenv/Scripts/python.exe price_indexr.py $DB_ID "SAPPHIRE RX 6600 XT PULSE -rig -minera -Notebook -PC -xiaomi -cooler"

Write-Output "Coletando preços da XFX RX 6600 XT SWFT 210..."
./pyenv/Scripts/python.exe price_indexr.py $DB_ID "XFX RX 6600 XT SWFT 210 -rig -minera -Notebook -PC -xiaomi -cooler"

Write-Output "Coletando preços da XFX RX 6600 XT QICK 319..."
./pyenv/Scripts/python.exe price_indexr.py $DB_ID "XFX RX 6600 XT QICK 319 -rig -minera -Notebook -PC -xiaomi -cooler"

Write-Output "Coletando preços da ASUS RX 6600 XT ROG STRIX OC..."
./pyenv/Scripts/python.exe price_indexr.py $DB_ID "ASUS RX 6600 XT ROG STRIX OC -rig -minera -Notebook -PC -xiaomi -cooler"

Write-Output "Coletando preços da ASUS RX 6600 XT DUAL..."
./pyenv/Scripts/python.exe price_indexr.py $DB_ID "ASUS RX 6600 XT DUAL -rig -minera -Notebook -PC -xiaomi -cooler"

# Gerar relatorio
$DB_PLACE = $pwd.Path + '\routines\data\' + $DB_ID + '.db'

Rscript.exe ./execute.R $DB_PLACE 12

# Notificar conclusao
#[reflection.assembly]::loadwithpartialname('System.Windows.Forms')
#[reflection.assembly]::loadwithpartialname('System.Drawing')
#$notify = new-object system.windows.forms.notifyicon
#$notify.icon = [System.Drawing.SystemIcons]::Information
#$notify.visible = $true
#$notify.showballoontip(10,'Script Executado','Script gpus_rtx_3060_ti.ps1 foi executado',[system.windows.forms.tooltipicon]::None)
