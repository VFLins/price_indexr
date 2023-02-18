# Coletar dados
Set-Location $PSScriptRoot
Set-Location ..
$DB_CON = 'geforce_rtx_3060_ti'

Write-Output "Coletando preços da EVGA RTX 3060 TI XC..."
./pyenv/Scripts/python.exe price_indexr.py $DB_CON "EVGA RTX 3060 TI XC -rig -minera -Notebook -PC -intel -xiaomi -cooler"

Write-Output "Coletando preços da ASUS RTX 3060 TI DUAL V2..."
./pyenv/Scripts/python.exe price_indexr.py $DB_CON "ASUS RTX 3060 TI DUAL V2 -rig -minera -Notebook -PC -intel -xiaomi -cooler"

Write-Output "Coletando preços da PALIT RTX 3060 TI DUAL..."
./pyenv/Scripts/python.exe price_indexr.py $DB_CON "PALIT RTX 3060 TI DUAL -rig -minera -Notebook -PC -intel -xiaomi -cooler"

Write-Output "Coletando preços da GALAX RTX 3060 Ti 1-Click Oc..."
./pyenv/Scripts/python.exe price_indexr.py $DB_CON "GALAX RTX 3060 TI CLICK OC -rig -minera -Notebook -PC -intel -xiaomi -cooler"

Write-Output "Coletando preços da MSI RTX 3060 TI VENTUS 2X..."
./pyenv/Scripts/python.exe price_indexr.py $DB_CON "MSI RTX 3060 TI VENTUS 2X -rig -minera -Notebook -PC -intel -xiaomi -cooler"

Write-Output "Coletando preços da ZOTAC RTX 3060 TI TWIN..."
./pyenv/Scripts/python.exe price_indexr.py $DB_CON "ZOTAC RTX 3060 TI TWIN -rig -minera -Notebook -PC -intel -xiaomi -cooler"

Write-Output "Coletando preços da GAINWARD RTX 3060 TI GHOST..."
./pyenv/Scripts/python.exe price_indexr.py $DB_CON "GAINWARD RTX 3060 TI GHOST -rig -minera -Notebook -PC -intel -xiaomi -cooler"

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
