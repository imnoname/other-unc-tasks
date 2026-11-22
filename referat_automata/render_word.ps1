param([Parameter(Mandatory=$true)][string]$InputDocx,
      [Parameter(Mandatory=$true)][string]$OutputPdf)
$ErrorActionPreference = 'Stop'
$sourcePath = (Resolve-Path -LiteralPath $InputDocx).Path
$pdfPath = [System.IO.Path]::GetFullPath($OutputPdf)
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$document = $null
try {
    $document = $word.Documents.Open($sourcePath, $false, $false)
    $document.Repaginate()
    foreach ($toc in $document.TablesOfContents) { $toc.Update() }
    $document.Fields.Update() | Out-Null
    foreach ($toc in $document.TablesOfContents) {
        $toc.Range.Font.Name = 'Times New Roman'
        $toc.Range.Font.Size = 12
        $toc.Range.ParagraphFormat.SpaceBefore = 0
        $toc.Range.ParagraphFormat.SpaceAfter = 0
        $toc.Range.ParagraphFormat.LineSpacingRule = 1
    }
    $document.Repaginate()
    foreach ($toc in $document.TablesOfContents) { $toc.UpdatePageNumbers() }
    $document.Save()
    $document.ExportAsFixedFormat($pdfPath, 17)
    Write-Output ('Pages: ' + $document.ComputeStatistics(2))
} finally {
    if ($null -ne $document) { $document.Close(0) }
    $word.Quit()
    [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($word)
}
