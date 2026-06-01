Set-Location -Path 'c:\Users\Parth Pandey\OneDrive\Documents\Projects\Quick Fix'

git add -A
$status = git status --porcelain
if ($status) {
    git commit -m 'add FastAPI backend at root, Dockerfile and docker-compose updates'
} else {
    Write-Host 'no changes to commit'
}

git push origin main
