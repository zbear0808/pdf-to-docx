# Merge DOCX files into one duplex-ready Word packet (needs Microsoft Word).
# Groups are separated by "|": each group starts on an odd page (section break), files inside a group
# follow with a page break. Each file keeps its own footer.
#   pwsh -File make_packet_docx.ps1 -Out "C:\...\Unit 2 Key Packet.docx" `
#        "L1 Key.docx" "L1 Practice Key.docx" "|" "L2 Key.docx" "L2 Practice Key.docx"
param([Parameter(Mandatory)][string]$Out, [Parameter(ValueFromRemainingArguments = $true)][string[]]$Files)
$ErrorActionPreference = "Stop"
$items = @(); $newGroup = $false
foreach ($f in $Files) {
    if ($f -eq "|") { $newGroup = $true; continue }
    $items += [pscustomobject]@{ Path = (Resolve-Path $f).Path; NewGroup = $newGroup }
    $newGroup = $false
}
$w = New-Object -ComObject Word.Application
$w.Visible = $false; $w.DisplayAlerts = 0
try {
    $doc = $w.Documents.Add($items[0].Path)
    for ($i = 1; $i -lt $items.Count; $i++) {
        $r = $doc.Content; $r.Collapse(0)
        $r.InsertBreak($(if ($items[$i].NewGroup) { 5 } else { 2 }))  # 5 = odd page, 2 = next page
        $r = $doc.Content; $r.Collapse(0)
        $r.InsertFile($items[$i].Path)
    }
    for ($i = 1; $i -lt $items.Count; $i++) {  # footers: otherwise every section inherits the first file's
        $src = $w.Documents.Open($items[$i].Path, $false, $true)
        $ft = $doc.Sections.Item($i + 1).Footers.Item(1)
        $ft.LinkToPrevious = $false
        $ft.Range.FormattedText = $src.Sections.Item(1).Footers.Item(1).Range.FormattedText
        $src.Close(0)
    }
    for ($k = 0; $k -lt 6; $k++) {  # InsertFile leaves empty paragraphs at the end -> blank last page
        $p = $doc.Paragraphs.Item($doc.Paragraphs.Count - 1)
        if ($p.Range.Text -match '^[\s\x07]*$' -and $p.Range.Tables.Count -eq 0) { $p.Range.Delete() | Out-Null } else { break }
    }
    $doc.SaveAs2($Out, 16)
    Write-Output "$([IO.Path]::GetFileName($Out)): $($doc.ComputeStatistics(2)) pages"
    $doc.Close(0)
} finally { $w.Quit() }
