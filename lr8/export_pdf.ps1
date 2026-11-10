$ErrorActionPreference = 'Stop'
$docx = Join-Path $PSScriptRoot 'report.docx'
$pdf = Join-Path $PSScriptRoot 'report.pdf'
$word = $null
$doc = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $doc = $word.Documents.Open($docx, $false, $false)
    $null = $doc.Fields.Update()
    for ($pass = 0; $pass -lt 2; $pass++) {
        if ($doc.TablesOfContents.Count -gt 0) { $null = $doc.TablesOfContents.Item(1).Update() }
        $null = $doc.Fields.Update()
    }
    $doc.Save()
    $doc.ExportAsFixedFormat($pdf, 17)
    Write-Output "Exported $pdf"
}
finally {
    if ($doc) { $doc.Close($false) }
    if ($word) { $word.Quit(); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) }
}
