Write-Host ""
Write-Host "==============================="
Write-Host " LUCID Brain Migration v1.0"
Write-Host "==============================="
Write-Host ""

$root = Get-Location

# ------------------------------------------
# Backup
# ------------------------------------------

$backup = Join-Path $root "backup_before_migration"

if (!(Test-Path $backup))
{
    Copy-Item src $backup -Recurse
    Write-Host "[OK] Backup Created"
}
else
{
    Write-Host "[SKIP] Backup Exists"
}

# ------------------------------------------
# Create Brain Folder
# ------------------------------------------

New-Item src\brain -ItemType Directory -Force | Out-Null

# ------------------------------------------
# Folder Migration
# ------------------------------------------

$folders = @(
    "attention",
    "context",
    "workspace",
    "emotion",
    "cognitive",
    "metacognition"
)

foreach($f in $folders)
{

    if(Test-Path "src\$f")
    {

        Write-Host "Moving $f..."

        Move-Item "src\$f" "src\brain\" -Force

    }

}

# ------------------------------------------
# Import Replace
# ------------------------------------------

$replace = @{

"src.attention"="src.brain.attention"
"src.context"="src.brain.context"
"src.workspace"="src.brain.workspace"
"src.emotion"="src.brain.emotion"
"src.cognitive"="src.brain.cognitive"
"src.metacognition"="src.brain.metacognition"

}

Get-ChildItem src -Recurse -Filter *.py | ForEach-Object {

    $content = Get-Content $_.FullName -Raw

    foreach($key in $replace.Keys)
    {
        $content = $content.Replace($key,$replace[$key])
    }

    Set-Content $_.FullName $content

}

Write-Host ""
Write-Host "[OK] Import Migration Complete"

# ------------------------------------------
# __init__
# ------------------------------------------

New-Item src\brain\__init__.py -ItemType File -Force | Out-Null

Write-Host ""
Write-Host "Migration Finished."