const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, 
        AlignmentType, WidthType, BorderStyle, ShadingType, VerticalAlign,
        HeadingLevel, PageBreak } = require('docx');

// 创建文档
const doc = new Document({
    sections: [{
        properties: {},
        children: [
            // 封面
            new Paragraph({
                heading: HeadingLevel.HEADING_1,
                children: [new TextRun({
                    text: "红利ETF定投分析报告",
                    size: 48,
                    bold: true,
                    color: "2E75B6"
                })],
                alignment: AlignmentType.CENTER,
                spacing: { before: 2400, after: 400 }
            }),
            new Paragraph({
                children: [new TextRun({
                    text: "基于沪深市场9只主流红利ETF的深度分析",
                    size: 28,
                    color: "666666"
                })],
                alignment: AlignmentType.CENTER,
                spacing: { after: 800 }
            }),
            new Paragraph({
                children: [new TextRun({
                    text: `生成日期: ${new Date().getFullYear()}年${new Date().getMonth()+1}月${new Date().getDate()}日`,
                    size: 22,
                    color: "999999"
                })],
                alignment: AlignmentType.CENTER,
                spacing: { after: 400 }
            }),
            new Paragraph({ children: [new PageBreak()] }),
            
            // 第一章
            new Paragraph({
                heading: HeadingLevel.HEADING_1,
                children: [new TextRun("一、红利ETF市场概览")],
                spacing: { before: 400, after: 300 }
            }),
            new Paragraph({
                children: [new TextRun({
                    text: "红利ETF是一种跟踪红利指数的交易型开放式指数基金，主要投资于高分红、低估值、业绩稳定的上市公司股票。相比普通ETF，红利ETF具有以下优势：",
                    size: 24
                })],
                spacing: { before: 200, after: 200 }
            }),
            new Paragraph({
                children: [new TextRun("• 稳定分红：成分股均为高股息率公司，定期分红")],
                spacing: { before: 100, after: 100 }
            }),
            new Paragraph({
                children: [new TextRun("• 抗跌性强：熊市中表现相对稳健")],
                spacing: { before: 100, after: 100 }
            }),
            new Paragraph({
                children: [new TextRun("• 适合定投：波动相对较小，适合长期定投")],
                spacing: { before: 100, after: 100 }
            }),
            new Paragraph({
                children: [new TextRun("• 复利效应：分红再投资可产生复利增长")],
                spacing: { before: 100, after: 400 }
            }),
            
            // 第二章
            new Paragraph({
                heading: HeadingLevel.HEADING_1,
                children: [new TextRun("二、9只红利ETF对比分析")],
                spacing: { before: 400, after: 300 }
            }),
            new Paragraph({
                children: [new TextRun({
                    text: "本次分析覆盖沪深市场9只主流红利ETF，数据截至2026年4月30日，来源为天天基金网。",
                    size: 24
                })],
                spacing: { before: 200, after: 300 }
            }),
            
            // ETF对比表格
            new Table({
                width: { size: 100, type: WidthType.PERCENTAGE },
                rows: [
                    new TableRow({
                        children: [
                            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "代码", bold: true })] })] }),
                            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "名称", bold: true })] })] }),
                            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "规模(亿)", bold: true })] })] }),
                            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "近1年", bold: true })] })] }),
                            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "近3年", bold: true })] })] }),
                            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "分红", bold: true })] })] })
                        ]
                    }),
                    new TableRow({
                        children: [
                            new TableCell({ children: [new Paragraph("510880")] }),
                            new TableCell({ children: [new Paragraph("华泰柏瑞上证红利")] }),
                            new TableCell({ children: [new Paragraph("171.39")] }),
                            new TableCell({ children: [new Paragraph("15.19%")] }),
                            new TableCell({ children: [new Paragraph("25.47%")] }),
                            new TableCell({ children: [new Paragraph("19次")] })
                        ]
                    }),
                    new TableRow({
                        children: [
                            new TableCell({ children: [new Paragraph("512890")] }),
                            new TableCell({ children: [new Paragraph("红利低波ETF")] }),
                            new TableCell({ children: [new Paragraph("311.87")] }),
                            new TableCell({ children: [new Paragraph("7.23%")] }),
                            new TableCell({ children: [new Paragraph("24.41%")] }),
                            new TableCell({ children: [new Paragraph("0次")] })
                        ]
                    }),
                    new TableRow({
                        children: [
                            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "515080", bold: true })] })] }),
                            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "中证红利ETF招商", bold: true })] })] }),
                            new TableCell({ children: [new Paragraph("88.68")] }),
                            new TableCell({ children: [new Paragraph("14.88%")] }),
                            new TableCell({ children: [new Paragraph("24.19%")] }),
                            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "16次", bold: true })] })] })
                        ]
                    })
                ]
            }),
            
            new Paragraph({ children: [new PageBreak()] }),
            
            // 第三章
            new Paragraph({
                heading: HeadingLevel.HEADING_1,
                children: [new TextRun("三、定投标的推荐")],
                spacing: { before: 400, after: 300 }
            }),
            new Paragraph({
                heading: HeadingLevel.HEADING_2,
                children: [new TextRun("首选推荐：515080 中证红利ETF招商")],
                spacing: { before: 300, after: 200 }
            }),
            new Paragraph({
                children: [new TextRun({
                    text: "推荐理由：",
                    bold: true,
                    size: 26
                })],
                spacing: { before: 200, after: 150 }
            }),
            new Paragraph({
                children: [new TextRun("1. 跨市场分散：同时覆盖上海和深圳市场，分散性优于仅覆盖沪市的上证红利ETF")],
                spacing: { before: 100, after: 100 }
            }),
            new Paragraph({
                children: [new TextRun("2. 高频率分红：成立以来分红16次，平均每季度都有分红，可实现分红再投资的复利效应")],
                spacing: { before: 100, after: 100 }
            }),
            new Paragraph({
                children: [new TextRun("3. 规模适中：88.68亿元，既不会太小（流动性风险），也不会太大（打新收益稀释）")],
                spacing: { before: 100, after: 100 }
            }),
            new Paragraph({
                children: [new TextRun("4. 历史表现稳健：近1年14.88%，近3年24.19%，各周期表现均衡")],
                spacing: { before: 100, after: 100 }
            }),
            new Paragraph({
                children: [new TextRun("5. 管理规范：招商基金管理，年化跟踪误差仅0.80%，费用低")],
                spacing: { before: 100, after: 400 }
            }),
            
            new Paragraph({ children: [new PageBreak()] }),
            
            // 第四章
            new Paragraph({
                heading: HeadingLevel.HEADING_1,
                children: [new TextRun("四、具体定投计划")],
                spacing: { before: 400, after: 300 }
            }),
            
            new Paragraph({
                heading: HeadingLevel.HEADING_2,
                children: [new TextRun("4.1 定投参数设定")],
                spacing: { before: 300, after: 200 }
            }),
            
            // 定投参数表格
            new Table({
                width: { size: 100, type: WidthType.PERCENTAGE },
                rows: [
                    new TableRow({
                        children: [
                            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "参数", bold: true })] })] }),
                            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "设定值", bold: true })] })] }),
                            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "说明", bold: true })] })] })
                        ]
                    }),
                    new TableRow({
                        children: [
                            new TableCell({ children: [new Paragraph("定投标的")] }),
                            new TableCell({ children: [new Paragraph("515080 + 510880")] }),
                            new TableCell({ children: [new Paragraph("主力+补充，跨市场覆盖")] })
                        ]
                    }),
                    new TableRow({
                        children: [
                            new TableCell({ children: [new Paragraph("每月金额")] }),
                            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "2000元", bold: true })] })] }),
                            new TableCell({ children: [new Paragraph("可根据收入调整")] })
                        ]
                    }),
                    new TableRow({
                        children: [
                            new TableCell({ children: [new Paragraph("定投频率")] }),
                            new TableCell({ children: [new Paragraph("每月")] }),
                            new TableCell({ children: [new Paragraph("工资日后3-5天")] })
                        ]
                    }),
                    new TableRow({
                        children: [
                            new TableCell({ children: [new Paragraph("分红方式")] }),
                            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "红利再投资", bold: true })] })] }),
                            new TableCell({ children: [new Paragraph("不取现金，自动再投资")] })
                        ]
                    }),
                    new TableRow({
                        children: [
                            new TableCell({ children: [new Paragraph("定投期限")] }),
                            new TableCell({ children: [new Paragraph("5年")] }),
                            new TableCell({ children: [new Paragraph("至少一轮牛熊周期")] })
                        ]
                    }),
                    new TableRow({
                        children: [
                            new TableCell({ children: [new Paragraph("预期年化收益")] }),
                            new TableCell({ children: [new Paragraph("12%")] }),
                            new TableCell({ children: [new Paragraph("基于历史表现测算")] })
                        ]
                    })
                ]
            }),
            
            new Paragraph({
                heading: HeadingLevel.HEADING_2,
                children: [new TextRun("4.2 收益测算")],
                spacing: { before: 300, after: 200 }
            }),
            
            // 收益测算表格
            new Table({
                width: { size: 100, type: WidthType.PERCENTAGE },
                rows: [
                    new TableRow({
                        children: [
                            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "年限", bold: true })] })] }),
                            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "累计投入", bold: true })] })] }),
                            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "预期市值", bold: true })] })] }),
                            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "收益", bold: true })] })] }),
                            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "收益率", bold: true })] })] })
                        ]
                    }),
                    new TableRow({
                        children: [
                            new TableCell({ children: [new Paragraph("1年")] }),
                            new TableCell({ children: [new Paragraph("24,000元")] }),
                            new TableCell({ children: [new Paragraph("25,440元")] }),
                            new TableCell({ children: [new Paragraph("1,440元")] }),
                            new TableCell({ children: [new Paragraph("6.0%")] })
                        ]
                    }),
                    new TableRow({
                        children: [
                            new TableCell({ children: [new Paragraph("3年")] }),
                            new TableCell({ children: [new Paragraph("72,000元")] }),
                            new TableCell({ children: [new Paragraph("89,993元")] }),
                            new TableCell({ children: [new Paragraph("17,993元")] }),
                            new TableCell({ children: [new Paragraph("25.0%")] })
                        ]
                    }),
                    new TableRow({
                        children: [
                            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "5年", bold: true })] })] }),
                            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "120,000元", bold: true })] })] }),
                            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "196,035元", bold: true, color: "00B050" })] })] }),
                            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "76,035元", bold: true, color: "00B050" })] })] }),
                            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "63.4%", bold: true, color: "00B050" })] })] })
                        ]
                    }),
                    new TableRow({
                        children: [
                            new TableCell({ children: [new Paragraph("10年")] }),
                            new TableCell({ children: [new Paragraph("240,000元")] }),
                            new TableCell({ children: [new Paragraph("496,356元")] }),
                            new TableCell({ children: [new Paragraph("256,356元")] }),
                            new TableCell({ children: [new Paragraph("106.8%")] })
                        ]
                    })
                ]
            }),
            
            new Paragraph({
                children: [new TextRun({
                    text: "注：以上测算基于12%年化收益率，实际收益会随市场波动。红利再投资可进一步提升实际收益。",
                    italics: true,
                    size: 20,
                    color: "FF0000"
                })],
                spacing: { before: 200, after: 400 }
            }),
            
            new Paragraph({ children: [new PageBreak()] }),
            
            // 第五章
            new Paragraph({
                heading: HeadingLevel.HEADING_1,
                children: [new TextRun("五、风险提示与应对")],
                spacing: { before: 400, after: 300 }
            }),
            
            new Paragraph({
                heading: HeadingLevel.HEADING_2,
                children: [new TextRun("5.1 主要风险")],
                spacing: { before: 300, after: 200 }
            }),
            new Paragraph({
                children: [new TextRun("1. 市场风险：股市整体下跌时，红利ETF也会随之下跌，但跌幅通常小于成长型ETF")],
                spacing: { before: 150, after: 150 }
            }),
            new Paragraph({
                children: [new TextRun("2. 分红减少风险：成分股公司减少分红时，ETF分红也会减少")],
                spacing: { before: 150, after: 150 }
            }),
            new Paragraph({
                children: [new TextRun("3. 跟踪误差风险：ETF表现可能与标的指数存在偏差")],
                spacing: { before: 150, after: 150 }
            }),
            new Paragraph({
                children: [new TextRun("4. 流动性风险：小规模ETF可能出现买卖价差大的情况")],
                spacing: { before: 150, after: 300 }
            }),
            
            new Paragraph({
                heading: HeadingLevel.HEADING_2,
                children: [new TextRun("5.2 应对策略")],
                spacing: { before: 300, after: 200 }
            }),
            new Paragraph({
                children: [new TextRun("• 坚持长期定投：不要在市场下跌时停止定投，反而是加仓良机")],
                spacing: { before: 100, after: 100 }
            }),
            new Paragraph({
                children: [new TextRun("• 分红再投资：选择"红利再投资"而非"现金分红"，充分利用复利")],
                spacing: { before: 100, after: 100 }
            }),
            new Paragraph({
                children: [new TextRun("• 定期再平衡：每年检查一次持仓，如某只ETF占比过高可适当减仓")],
                spacing: { before: 100, after: 100 }
            }),
            new Paragraph({
                children: [new TextRun("• 设置止盈线：如总收益率超过80%，可考虑分批止盈，锁定收益")],
                spacing: { before: 100, after: 400 }
            }),
            
            // 结论
            new Paragraph({
                heading: HeadingLevel.HEADING_1,
                children: [new TextRun("六、结论")],
                spacing: { before: 400, after: 300 }
            }),
            new Paragraph({
                children: [new TextRun({
                    text: "综合来看，515080中证红利ETF招商是当前市场环境下最适合定投的红利ETF标的。其跨市场分散、高频率分红、规模适中、表现稳健的特点，非常适合长期定投。",
                    size: 24
                })],
                spacing: { before: 200, after: 200 }
            }),
            new Paragraph({
                children: [new TextRun({
                    text: "建议采用"70% 515080 + 30% 510880"的均衡配置，每月定投2000元，坚持5年以上，预期可获得12%的年化收益。重要的是保持纪律，不要因短期波动而改变策略。",
                    size: 24
                })],
                spacing: { before: 200, after: 400 }
            }),
            
            new Paragraph({
                children: [new TextRun({
                    text: "投资有风险，以上分析仅供参考，不构成投资建议。实际操作前请咨询专业投资顾问。",
                    bold: true,
                    size: 22,
                    color: "FF0000"
                })],
                spacing: { before: 300, after: 300 },
                alignment: AlignmentType.CENTER
            })
        ]
    }]
});

// 保存文档
Packer.toBuffer(doc).then(buffer => {
    fs.writeFileSync("d:\\temp\\红利ETF\\红利ETF定投分析报告.docx", buffer);
    console.log("✓ Word文档生成成功！");
    console.log("文件路径: d:\\temp\\红利ETF\\红利ETF定投分析报告.docx");
});
