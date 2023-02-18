# Coletar dados
Set-Destination C:/Users/vflin/Price_indexr
$DB_CON = 'radeon_rx_6600'

Write-Output "Coletando preços da ASUS RADEON RX 6600 DUAL..."
./pyenv/Scripts/python.exe price_indexr.py $DB_CON "ASUS DUAL RADEON RX 6600 -rig -minera -XT -Notebook -PC -xiaomi -cooler"

Write-Output "Coletando preços da MSI RADEON RX 6600 MECH 2X OC..."
./pyenv/Scripts/python.exe price_indexr.py $DB_CON "MSI RADEON RX 6600 MECH 2X OC -rig -minera -XT -Notebook -PC -xiaomi -cooler"

Write-Output "Coletando preços da ASROCK RADEON RX 6600 CHALLENGER..."
./pyenv/Scripts/python.exe price_indexr.py $DB_CON "ASROCK RADEON RX 6600 CHALLENGER -rig -minera -XT -Notebook -PC -xiaomi -cooler"

Write-Output "Coletando preços da SAPPHIRE RX 6600 RADEON PULSE..."
./pyenv/Scripts/python.exe price_indexr.py $DB_CON "SAPPHIRE RX 6600 RADEON PULSE -rig -minera -XT -Notebook -PC -xiaomi -cooler"

Write-Output "Coletando preços da XFX RADEON RX 6600 SWFT 210..."
./pyenv/Scripts/python.exe price_indexr.py $DB_CON "XFX RADEON RX 6600 SWFT 210 -rig -minera -XT -Notebook -PC -xiaomi -cooler"

Write-Output "Coletando preços da GIGABYTE RADEON RX 6600 EAGLE..."
./pyenv/Scripts/python.exe price_indexr.py $DB_CON "GIGABYTE RADEON RX 6600 EAGLE -rig -minera -XT -Notebook -PC -xiaomi -cooler"

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
