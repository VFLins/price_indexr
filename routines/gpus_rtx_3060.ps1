# Coletar dados
Set-Location $PSScriptRoot
Set-Location ..
$DB_CON = 'geforce_rtx_3060'

Write-Output "Coletando preços da ASUS RTX 3060 TUF..."
./pyenv/Scripts/python.exe price_indexr.py $DB_CON "ASUS RTX 3060 TUF -TI -rig -minera -Notebook -PC -intel -xiaomi -cooler"

Write-Output "Coletando preços da ASUS RTX 3060 DUAL..."
./pyenv/Scripts/python.exe price_indexr.py $DB_CON "ASUS RTX 3060 DUAL -TI -rig -minera -Notebook -PC -intel -xiaomi -cooler"

Write-Output "Coletando preços da MSI RTX 3060 VENTUS 2X..."
./pyenv/Scripts/python.exe price_indexr.py $DB_CON "MSI RTX 3060 VENTUS 2X -TI -rig -minera -Notebook -PC -intel -xiaomi -cooler"

Write-Output "Coletando preços da MSI RTX 3060 VENTUS 3X..."
./pyenv/Scripts/python.exe price_indexr.py $DB_CON "MSI RTX 3060 VENTUS 3X -TI -rig -minera -Notebook -PC -intel -xiaomi -cooler"

Write-Output "Coletando preços da XFX PALIT RTX 3060 DUAL..."
./pyenv/Scripts/python.exe price_indexr.py $DB_CON "PALIT RTX 3060 DUAL -TI -rig -minera -Notebook -PC -intel -xiaomi -cooler"

Write-Output "Coletando preços da GALAX RTX 3060 CLICK OC..."
./pyenv/Scripts/python.exe price_indexr.py $DB_CON "GALAX RTX 3060 CLICK OC -TI -rig -minera -Notebook -PC -intel -xiaomi -cooler"

Write-Output "Coletando preços da ZOTAC RTX 3060 TWIN EDGE..."
./pyenv/Scripts/python.exe price_indexr.py $DB_CON "ZOTAC RTX 3060 TWIN EDGE -TI -rig -minera -Notebook -PC -intel -xiaomi -cooler"

Write-Output "Coletando preços da PNY RTX 3060 REVEL EPIC-X..."
./pyenv/Scripts/python.exe price_indexr.py $DB_CON "PNY RTX 3060 REVEL EPIC -TI -rig -minera -Notebook -PC -intel -xiaomi -cooler"

Write-Output "Coletando preços da GAINWARD RTX 3060 GHOST..."
./pyenv/Scripts/python.exe price_indexr.py $DB_CON "GAINWARD RTX 3060 GHOST -TI -rig -minera -Notebook -PC -intel -xiaomi -cooler"

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
