<#
.SYNOPSIS
红利ETF资料收集脚本 (PowerShell版本)
.DESCRIPTION
收集沪深市场红利ETF的名称、代码、净值、收益率等资料
#>

Write-Host "=========================================="
Write-Host "红利ETF资料收集工具"
Write-Host "=========================================="

# 定义常见红利ETF列表
$presetETF = @(
    @{代码="510880"; 名称="华泰柏瑞上证红利ETF"},
    @{代码="159905"; 名称="工银深证红利ETF"},
    @{代码="515450"; 名称="招商中证红利ETF"},
    @{代码="512530"; 名称="建信沪深300红利ETF"},
    @{代码="515080"; 名称="中证红利低波动ETF"},
    @{代码="515100"; 名称="红利低波100ETF"},
    @{代码="512890"; 名称="红利低波ETF"},
    @{代码="515300"; 名称="嘉实沪深300红利低波动ETF"}
)

Write-Host "`n开始收集红利ETF数据..."
Write-Host "共 $($presetETF.Count) 只红利ETF需要分析"

$results = @()

foreach ($etf in $presetETF) {
    $code = $etf.代码
    $name = $etf.名称
    
    Write-Host "`n处理 $code - $name"
    
    # 构建新浪财经API URL
    if ($code.StartsWith("6") -or $code.StartsWith("5")) {
        $symbol = "sh$code"
    } else {
        $symbol = "sz$code"
    }
    
    $url = "http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
    $fullUrl = "$url`?symbol=$symbol&scale=240&ma=no&datalen=300"
    
    try {
        # 获取历史数据
        $response = Invoke-RestMethod -Uri $fullUrl -TimeoutSec 30
        
        if ($response -and $response.Count -gt 0) {
            # 解析数据并排序
            $data = $response | Where-Object { $_ -and $_.day } | Sort-Object { [DateTime]$_.day }
            
            $latestPrice = [float]$data[-1].close
            
            # 计算年度收益率（假设252个交易日=1年）
            $yearAgoIndex = [Math]::Max(0, $data.Count - 252)
            $yearAgoPrice = [float]$data[$yearAgoIndex].close
            $annualReturn = (($latestPrice - $yearAgoPrice) / $yearAgoPrice) * 100
            
            # 计算今年以来收益率
            $thisYear = (Get-Date).Year
            $thisYearData = $data | Where-Object { [DateTime]$_.day -ge "$thisYear-01-01" }
            if ($thisYearData -and $thisYearData.Count -gt 0) {
                $ytdPrice = [float]$thisYearData[0].close
                $ytdReturn = (($latestPrice - $ytdPrice) / $ytdPrice) * 100
            } else {
                $ytdReturn = 0
            }
            
            $result = [PSCustomObject]@{
                代码 = $code
                名称 = $name
                "最新净值" = [math]::Round($latestPrice, 3)
                "年度收益率(%)" = [math]::Round($annualReturn, 2)
                "今年以来收益率(%)" = [math]::Round($ytdReturn, 2)
            }
            
            Write-Host "  最新净值: $($result.'最新净值') 元"
            Write-Host "  年度收益率: $($result.'年度收益率(%)')%"
        } else {
            $result = [PSCustomObject]@{
                代码 = $code
                名称 = $name
                "最新净值" = "N/A"
                "年度收益率(%)" = "N/A"
                "今年以来收益率(%)" = "N/A"
            }
        }
    } catch {
        Write-Host "  获取失败: $_"
        $result = [PSCustomObject]@{
            代码 = $code
            名称 = $name
            "最新净值" = "N/A"
            "年度收益率(%)" = "N/A"
            "今年以来收益率(%)" = "N/A"
        }
    }
    
    $results += $result
    Start-Sleep -Milliseconds 300
}

# 保存结果
Write-Host "`n=========================================="
Write-Host "保存结果..."

# 保存为CSV
$csvPath = "d:\temp\红利ETF\红利ETF资料汇总.csv"
$results | Export-Csv -Path $csvPath -NoTypeInformation -Encoding UTF8
Write-Host "CSV已保存: $csvPath"

# 打印汇总
Write-Host "`n=========================================="
Write-Host "红利ETF汇总信息:"
Write-Host "=========================================="
$results | Format-Table -AutoSize

Write-Host "`n=========================================="
Write-Host "资料收集完成！"
Write-Host "=========================================="
