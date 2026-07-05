#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定投系统Web版本
基于Flask的Web界面
"""

from flask import Flask, render_template_string, jsonify, request
import sys
import os
import webbrowser
import threading
import time

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

# 添加 CORS 支持（允许跨域访问）
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# HTML模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>平衡型定投系统 v1.0</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }

        .nav {
            background: #f8f9fa;
            padding: 15px 30px;
            display: flex;
            justify-content: center;
            gap: 10px;
            flex-wrap: wrap;
            border-bottom: 1px solid #ddd;
        }

        .nav button {
            padding: 12px 25px;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s;
            background: white;
            color: #667eea;
            border: 2px solid #667eea;
        }

        .nav button:hover {
            background: #667eea;
            color: white;
        }

        .nav button.active {
            background: #667eea;
            color: white;
        }

        .content {
            padding: 30px;
        }

        .section {
            display: none;
        }

        .section.active {
            display: block;
        }

        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }

        .card h2 {
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }

        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .info-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }

        .info-item h3 {
            color: #667eea;
            font-size: 0.9em;
            margin-bottom: 5px;
        }

        /* Edit form inputs */
        #config-edit-table input,
        #config-edit-table select,
        #system-params-form input {
            padding: 6px 8px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 0.9em;
        }

        #config-edit-table input:focus,
        #config-edit-table select:focus,
        #system-params-form input:focus {
            border-color: #667eea;
            outline: none;
        }

        .form-row {
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .form-row label {
            min-width: 150px;
            font-weight: 500;
        }

        .form-row input {
            flex: 1;
            max-width: 200px;
        }

        .btn-sm {
            padding: 5px 12px !important;
            font-size: 0.85em !important;
            margin-left: 10px;
            vertical-align: middle;
        }

        .info-item p {
            font-size: 1.5em;
            font-weight: bold;
            color: #333;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }

        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }

        th {
            background: #667eea;
            color: white;
            font-weight: bold;
        }

        tr:hover {
            background: #f8f9fa;
        }

        .btn {
            padding: 12px 25px;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s;
            background: #667eea;
            color: white;
        }

        .btn:hover {
            background: #764ba2;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }

        .btn-success {
            background: #28a745;
        }

        .btn-success:hover {
            background: #218838;
        }

        .btn-warning {
            background: #ffc107;
            color: #333;
        }

        .btn-warning:hover {
            background: #e0a800;
        }

        .loading {
            text-align: center;
            padding: 50px;
        }

        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .status-ok {
            color: #d32f2f;
            font-weight: bold;
        }

        .status-error {
            color: #2e7d32;
            font-weight: bold;
        }

        .status-warning {
            color: #ffc107;
            font-weight: bold;
        }

        .config-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }

        .config-item {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }

        .config-item .code {
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .config-item .name {
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
        }

        .config-item .amount {
            font-size: 1.5em;
            font-weight: bold;
        }

        .config-item .percent {
            font-size: 0.8em;
            opacity: 0.8;
        }

        .calendar {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
            gap: 10px;
        }

        .calendar-day {
            background: #f8f9fa;
            padding: 10px;
            border-radius: 8px;
            text-align: center;
        }

        .calendar-day.trading {
            background: #d4edda;
            color: #155724;
        }

        .calendar-day.first {
            background: #667eea;
            color: white;
            font-weight: bold;
        }

        .calendar-day.today {
            border: 3px solid #ffc107;
        }

        .footer {
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }

        .alert {
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 15px;
        }

        .alert-info {
            background: #d1ecf1;
            border-left: 4px solid #17a2b8;
            color: #0c5460;
        }

        .alert-success {
            background: #d4edda;
            border-left: 4px solid #28a745;
            color: #155724;
        }

        .alert-warning {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            color: #856404;
        }

        .alert-error {
            background: #f8d7da;
            border-left: 4px solid #dc3545;
            color: #721c24;
        }

        .history-list {
            max-height: 500px;
            overflow-y: auto;
        }

        .history-item {
            background: #f8f9fa;
            padding: 8px 12px;
            border-radius: 6px;
            margin-bottom: 6px;
            border-left: 3px solid #667eea;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .history-item .date {
            color: #667eea;
            font-weight: 500;
            font-size: 0.8em;
            min-width: 140px;
            flex-shrink: 0;
        }

        .history-item .details {
            color: #555;
            font-size: 0.82em;
            flex: 1;
            padding-left: 15px;
        }

        /* 持仓编辑样式 */
        .edit-input {
            width: 80px;
            padding: 4px 6px;
            border: 1px solid #667eea;
            border-radius: 4px;
            font-size: 0.9em;
            text-align: right;
        }

        .edit-input:focus {
            outline: none;
            border-color: #764ba2;
            box-shadow: 0 0 3px rgba(102, 126, 234, 0.5);
        }

        .edit-row {
            background: #fff8e1 !important;
        }

        .action-cell {
            white-space: nowrap;
        }

        .action-cell .btn {
            padding: 4px 10px;
            font-size: 0.8em;
            margin-right: 5px;
        }

        /* 标的检讨样式 */
        .review-item {
            display: flex;
            align-items: center;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
            border-left: 4px solid #667eea;
            background: #f8f9fa;
        }
        .review-item .code-name {
            min-width: 150px;
            font-weight: bold;
        }
        .review-item .numbers {
            min-width: 200px;
            text-align: right;
            margin-right: 20px;
        }
        .review-item .suggestion {
            flex: 1;
            font-size: 0.9em;
            color: #555;
        }
        .review-item.status-danger { border-left-color: #d32f2f; background: #fff5f5; }
        .review-item.status-warn   { border-left-color: #f57c00; background: #fff8e1; }
        .review-item.status-good   { border-left-color: #388e3c; background: #f1f8e9; }
        .review-item.status-ok     { border-left-color: #1976d2; background: #e3f2fd; }
        .review-item.status-empty  { border-left-color: #9e9e9e; background: #f5f5f5; }
        .review-status-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8em;
            margin-left: 8px;
        }
        .review-status-badge.danger { background: #d32f2f; color: white; }
        .review-status-badge.warn   { background: #f57c00; color: white; }
        .review-status-badge.good   { background: #388e3c; color: white; }
        .review-status-badge.ok     { background: #1976d2; color: white; }
        .review-status-badge.empty  { background: #9e9e9e; color: white; }

        @media (max-width: 768px) {
            .header h1 {
                font-size: 1.8em;
            }

            .nav {
                padding: 10px;
            }

            .nav button {
                padding: 10px 15px;
                font-size: 0.9em;
            }

            .content {
                padding: 15px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>平衡型定投系统</h1>
            <p>基于方案2：适合大多数年轻人的定投策略</p>
        </div>

        <div class="nav">
            <button onclick="showSection('home')" class="active" id="btn-home">首页</button>
            <button onclick="showSection('portfolio')" id="btn-portfolio">持仓</button>
            <button onclick="showSection('config')" id="btn-config">配置</button>
            <button onclick="showSection('review')" id="btn-review">检讨</button>
            <button onclick="showSection('calendar')" id="btn-calendar">日历</button>
            <button onclick="showSection('history')" id="btn-history">历史</button>
            <button onclick="showSection('diagnose')" id="btn-diagnose">诊断</button>
            <button onclick="showSection('backtest')" id="btn-backtest">📈 回测</button>
            <button onclick="window.location.href='/stop_profit'" style="background:#e74c3c;color:white;border-color:#e74c3c">🔄 止盈轮动</button>
        </div>

        <div class="content">
            <!-- 首页 -->
            <div id="section-home" class="section active">
                <div class="card">
                    <h2>系统状态</h2>
                    <div class="info-grid">
                        <div class="info-item">
                            <h3>当前月份</h3>
                            <p id="current-month">加载中...</p>
                        </div>
                        <div class="info-item">
                            <h3>本月交易日</h3>
                            <p id="trading-days-count">加载中...</p>
                        </div>
                        <div class="info-item">
                            <h3>是否为首交易日</h3>
                            <p id="is-first-day">加载中...</p>
                        </div>
                        <div class="info-item">
                            <h3>总投入金额</h3>
                            <p id="total-invested">¥0.00</p>
                        </div>
                        <div class="info-item">
                            <h3>当前策略</h3>
                            <p id="current-strategy">加载中...</p>
                        </div>
                    </div>
                    <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:10px;">
                        <button class="btn btn-success" onclick="runDCA()" id="btn-run-dca">执行月度定投</button>
                        <button class="btn" onclick="toggleStrategy()" id="btn-toggle-strategy"
                                title="切换到价值平均法">切换策略</button>
                    </div>
                </div>

                <div class="card">
                    <h2>快速操作</h2>
                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                        <button class="btn" onclick="checkPortfolio()">查看持仓</button>
                        <button class="btn btn-warning" onclick="exportData()">导出数据</button>
                        <button class="btn" onclick="refreshData()">刷新数据</button>
                    </div>
                </div>

                <div class="card">
                    <h2>ETF配置概览</h2>
                    <div class="config-list" id="config-overview">
                        <!-- 动态生成 -->
                    </div>
                </div>
            </div>

            <!-- 持仓页面 -->
            <div id="section-portfolio" class="section">
                <div class="card">
                    <h2>当前持仓
                        <button class="btn btn-sm" id="btn-edit-portfolio" onclick="togglePortfolioEdit()">编辑</button>
                        <button class="btn btn-success btn-sm" id="btn-save-portfolio" onclick="savePortfolioChanges()" style="display:none">保存</button>
                        <button class="btn btn-sm" id="btn-cancel-portfolio" onclick="cancelPortfolioEdit()" style="display:none">取消</button>
                    </h2>
                    <div id="portfolio-table">
                        <div class="loading">
                            <div class="spinner"></div>
                            <p>加载中...</p>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <h2>收益统计</h2>
                    <div class="info-grid" id="profit-stats">
                        <div class="info-item">
                            <h3>总投入</h3>
                            <p id="stat-invested">¥0.00</p>
                        </div>
                        <div class="info-item">
                            <h3>当前市值</h3>
                            <p id="stat-value">¥0.00</p>
                        </div>
                        <div class="info-item">
                            <h3>总盈亏</h3>
                            <p id="stat-profit">¥0.00</p>
                        </div>
                        <div class="info-item">
                            <h3>收益率</h3>
                            <p id="stat-return">0.00%</p>
                        </div>
                        <div class="info-item" style="background:#e8f5e9;">
                            <h3>现金余额</h3>
                            <p id="stat-cash" style="color:#2e7d32;">¥0.00</p>
                        </div>
                        <div class="info-item" style="background:#fff3e0;">
                            <h3>总资产</h3>
                            <p id="stat-total">¥0.00</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 配置页面 -->
            <div id="section-config" class="section">
                <div class="card">
                    <h2>定投配置</h2>
                    <div style="margin-bottom: 15px;">
                        <button class="btn btn-primary" onclick="toggleEdit()">编辑配置</button>
                    </div>
                    <form id="config-form" style="display: none;">
                        <table>
                            <thead>
                                <tr>
                                    <th>代码</th>
                                    <th>名称</th>
                                    <th>类别</th>
                                    <th>占比(%)</th>
                                    <th>每月金额(¥)</th>
                                </tr>
                            </thead>
                            <tbody id="config-edit-table">
                            </tbody>
                        </table>
                        <div style="margin-top: 15px;">
                            <button type="button" class="btn btn-success" onclick="saveConfig()">保存配置</button>
                            <button type="button" class="btn" onclick="cancelEdit()">取消</button>
                        </div>
                    </form>
                    <table id="config-view-table">
                        <thead>
                            <tr>
                                <th>代码</th>
                                <th>名称</th>
                                <th>类别</th>
                                <th>占比</th>
                                <th>每月金额</th>
                            </tr>
                        </thead>
                        <tbody id="config-table">
                        </tbody>
                    </table>
                </div>

                <div class="card">
                    <h2>系统参数 <button class="btn btn-sm" onclick="toggleSystemParamsEdit()">编辑</button></h2>
                    <form id="system-params-form" style="display: none; margin-top: 15px;">
                        <div class="form-row">
                            <label>每月定投总额 (¥):</label>
                            <input type="number" id="edit-monthly-amount" min="1000" step="100">
                        </div>
                        <div class="form-row">
                            <label>交易佣金费率 (%):</label>
                            <input type="number" id="edit-commission-rate" min="0.001" max="0.1" step="0.001">
                        </div>
                        <div class="form-row">
                            <label>最低佣金 (¥):</label>
                            <input type="number" id="edit-min-commission" min="0" step="0.1">
                        </div>
                        <div class="form-row">
                            <label>最小交易单位 (股):</label>
                            <input type="number" id="edit-min-shares" min="100" step="100">
                        </div>
                        <div style="margin-top: 15px;">
                            <button type="button" class="btn btn-success btn-sm" onclick="saveSystemParams()">保存</button>
                            <button type="button" class="btn btn-sm" onclick="cancelSystemParamsEdit()">取消</button>
                        </div>
                    </form>
                    <div class="info-grid" id="system-params-view">
                        <div class="info-item">
                            <h3>每月定投总额</h3>
                            <p id="total-amount">¥3,000</p>
                        </div>
                        <div class="info-item">
                            <h3>交易佣金费率</h3>
                            <p id="commission-rate">0.01%</p>
                        </div>
                        <div class="info-item">
                            <h3>最低佣金</h3>
                            <p id="min-commission">¥5.00 (不足5元按5元收)</p>
                        </div>
                        <div class="info-item">
                            <h3>最小交易单位</h3>
                            <p id="min-shares">100股</p>
                        </div>
                        <div class="info-item">
                            <h3>ETF数量</h3>
                            <p id="etf-count">6只</p>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="alert alert-info">
                        <strong>方案说明：</strong>本系统采用平衡型定投方案，适合有一定风险承受能力的年轻投资者。
                        通过分散配置红利ETF、宽基指数、行业主题和海外资产，实现收益与风险的平衡。
                    </div>
                </div>
            </div>

            <!-- 标的检讨 -->
            <div id="section-review" class="section">
                <div class="card">
                    <h2>标的物检讨 <span style="font-size:0.6em;color:#999;font-weight:normal;">· 行业ETF专题</span></h2>
                    <div id="review-industry">
                        <div class="loading"><div class="spinner"></div><p>加载中...</p></div>
                    </div>
                </div>

                <div class="card">
                    <h2>类别配置平衡</h2>
                    <div id="review-balance">
                        <div class="loading"><div class="spinner"></div><p>加载中...</p></div>
                    </div>
                </div>

                <div class="card">
                    <h2>总结</h2>
                    <div id="review-summary" class="alert">
                        加载中...
                    </div>
                </div>
            </div>

            <!-- 日历页面 -->
            <div id="section-calendar" class="section">
                <div class="card">
                    <h2>本月交易日历</h2>
                    <div id="calendar-month"></div>
                    <div class="calendar" id="calendar-grid">
                        <!-- 动态生成 -->
                    </div>
                </div>

                <div class="card">
                    <h2>交易日信息</h2>
                    <div class="info-grid">
                        <div class="info-item">
                            <h3>首交易日</h3>
                            <p id="first-trading-day">-</p>
                        </div>
                        <div class="info-item">
                            <h3>末交易日</h3>
                            <p id="last-trading-day">-</p>
                        </div>
                        <div class="info-item">
                            <h3>交易日总数</h3>
                            <p id="total-trading-days">-</p>
                        </div>
                        <div class="info-item">
                            <h3>今日日期</h3>
                            <p id="today-date">-</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 历史页面 -->
            <div id="section-history" class="section">
                <div class="card">
                    <h2>交易历史</h2>
                    <div class="history-list" id="history-list">
                        <p>暂无交易记录</p>
                    </div>
                </div>
            </div>

            <!-- 诊断页面 -->
            <div id="section-diagnose" class="section">
                <div class="card">
                    <h2>系统诊断</h2>
                    <div id="diagnose-results">
                        <button class="btn" onclick="runDiagnose()">运行诊断</button>
                    </div>
                </div>

                <div class="card">
                    <h2>依赖检查</h2>
                    <div id="dependency-check">
                        <p>点击"运行诊断"检查依赖库状态</p>
                    </div>
                </div>

                <div class="card">
                    <h2>安装依赖</h2>
                    <div class="alert alert-info">
                        <p>如果诊断发现问题，请打开命令提示符运行：</p>
                        <code style="background: #e9ecef; padding: 5px 10px; border-radius: 5px; display: block; margin-top: 10px;">
                            pip install akshare pandas python-docx schedule chinese-calendar flask
                        </code>
                    </div>
                </div>
            </div>

            <!-- 回测对比 -->
            <div id="section-backtest" class="section">
                <div class="card">
                    <h2>📈 策略回测对比 (DCA vs VA)</h2>
                    <p style="color:#666;font-size:13px;margin-bottom:15px;">
                        对比每月定投 (DCA) 与价值平均法 (VA) 在历史区间的表现。<br>
                        <strong>DCA</strong>：每月固定金额买入，简单稳定。<br>
                        <strong>VA</strong>：每月持仓目标市值按固定金额增长，自动"跌多买多、涨多卖出"。
                    </p>

                    <div style="display:flex;gap:10px;align-items:flex-end;flex-wrap:wrap;margin-bottom:15px;">
                        <div>
                            <label style="display:block;font-size:13px;margin-bottom:4px;">开始日期</label>
                            <input type="date" id="bt-start" value="2024-06-01" style="padding:6px;border-radius:4px;border:1px solid #ccc;">
                        </div>
                        <div>
                            <label style="display:block;font-size:13px;margin-bottom:4px;">结束日期</label>
                            <input type="date" id="bt-end" value="2026-07-04" style="padding:6px;border-radius:4px;border:1px solid #ccc;">
                        </div>
                        <div>
                            <label style="display:block;font-size:13px;margin-bottom:4px;">每月金额(¥)</label>
                            <input type="number" id="bt-amount" value="3000" style="padding:6px;border-radius:4px;border:1px solid #ccc;width:100px;">
                        </div>
                        <div>
                            <label style="display:block;font-size:13px;margin-bottom:4px;">止盈阈值(%)</label>
                            <input type="number" id="bt-threshold" value="20" step="5" style="padding:6px;border-radius:4px;border:1px solid #ccc;width:80px;">
                        </div>
                        <button class="btn" onclick="runBacktest()" id="btn-run-bt"
                                style="background:#27ae60;color:white;border-color:#27ae60;padding:8px 20px;">
                            运行回测
                        </button>
                    </div>

                    <div id="bt-results" style="margin-top:20px;">
                        <p style="color:#999;">点击"运行回测"开始对比...</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>平衡型定投系统 v1.0 | 基于方案2 | 适合年轻投资者</p>
            <p>投资有风险，定投需谨慎</p>
        </div>
    </div>

    <script>
        // 持仓请求控制器（防止切换标签时请求堆积）
        let portfolioCtrl = null;
        let portfolioData = null;  // 缓存持仓数据

        // 显示指定板块
        function showSection(sectionId) {
            // 隐藏所有板块
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            // 取消所有按钮的active状态
            document.querySelectorAll('.nav button').forEach(b => b.classList.remove('active'));

            // 显示指定板块
            document.getElementById('section-' + sectionId).classList.add('active');
            document.getElementById('btn-' + sectionId).classList.add('active');

            // 加载数据
            if (sectionId === 'portfolio') loadPortfolio();
            if (sectionId === 'history') loadHistory();
            if (sectionId === 'review') loadReview();
            if (sectionId === 'calendar') loadCalendar();
        }

        // 运行回测对比
        function runBacktest() {
            const start = document.getElementById('bt-start').value;
            const end = document.getElementById('bt-end').value;
            const amount = parseFloat(document.getElementById('bt-amount').value) || 3000;
            const threshold = (parseFloat(document.getElementById('bt-threshold').value) || 20) / 100;

            const btn = document.getElementById('btn-run-bt');
            const orig = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '⏳ 回测中...';
            document.getElementById('bt-results').innerHTML = '<p style="color:#666;">正在加载历史K线和模拟交易，请稍候...</p>';

            fetch('/api/backtest/compare', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({start, end, amount, threshold})
            })
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    document.getElementById('bt-results').innerHTML = `<div class="alert alert-error">${data.error}</div>`;
                    return;
                }
                renderBacktestResults(data);
            })
            .catch(err => {
                document.getElementById('bt-results').innerHTML = `<div class="alert alert-error">请求失败: ${err}</div>`;
            })
            .finally(() => {
                btn.disabled = false;
                btn.innerHTML = orig;
            });
        }

        function fmtMoney(v, sign=false) {
            if (v == null || isNaN(v)) return '-';
            const n = Number(v);
            const s = sign && n >= 0 ? '+' : '';
            return s + '¥' + n.toLocaleString('zh-CN', {minimumFractionDigits:2, maximumFractionDigits:2});
        }
        function fmtPct(v, sign=true) {
            if (v == null || isNaN(v)) return '-';
            const s = sign && Number(v) >= 0 ? '+' : '';
            return s + Number(v).toFixed(2) + '%';
        }
        function colorCell(v, threshold=0, mode='auto') {
            // mode: 'auto' 红涨绿跌，'inverse' 反过来（回撤越小越好）
            const n = Number(v);
            if (mode === 'inverse') return n <= threshold ? 'color:#16a085;' : 'color:#c0392b;';
            return n >= threshold ? 'color:#c0392b;' : 'color:#16a085;';
        }

        function renderBacktestResults(data) {
            const dca = data.dca || {};
            const va = data.va || {};
            const rows = [
                {label:'总投入',       dca:dca.total_invested,    va:va.total_invested,    fmt:'money'},
                {label:'期末价值',     dca:dca.final_value,       va:va.final_value,       fmt:'money'},
                {label:'总收益',       dca:dca.total_return,      va:va.total_return,      fmt:'moneySigned'},
                {label:'总收益率',     dca:dca.total_return_pct,  va:va.total_return_pct,  fmt:'pct'},
                {label:'年化收益率',   dca:dca.annual_return_pct, va:va.annual_return_pct, fmt:'pct'},
                {label:'夏普比率',     dca:dca.sharpe_ratio,      va:va.sharpe_ratio,      fmt:'number'},
                {label:'最大回撤',     dca:dca.max_drawdown_pct,  va:va.max_drawdown_pct,  fmt:'pctInverse'},
                {label:'定投次数',     dca:dca.dca_count,         va:va.dca_count,         fmt:'int'},
                {label:'止盈触发次数', dca:dca.stop_profit_count, va:va.stop_profit_count, fmt:'int'},
                {label:'总交易次数',   dca:dca.trade_count||'-',  va:va.trade_count||'-',  fmt:'int'},
            ];

            let html = '<h3 style="margin-top:20px;">📊 回测结果</h3>';
            html += `<p style="color:#666;font-size:13px;">区间 ${data.start_date} ~ ${data.end_date} | 每月 ¥${data.amount} | 止盈阈值 ${(data.threshold*100).toFixed(0)}%</p>`;

            // 对比表格
            html += '<table style="width:100%;border-collapse:collapse;margin-top:15px;font-size:14px;">';
            html += '<tr style="background:#34495e;color:white;">';
            html += '<th style="padding:10px;text-align:left;">指标</th>';
            html += '<th style="padding:10px;text-align:right;">DCA 定投</th>';
            html += '<th style="padding:10px;text-align:right;">VA 价值平均</th>';
            html += '<th style="padding:10px;text-align:right;">差异 (VA-DCA)</th>';
            html += '</tr>';

            rows.forEach(r => {
                let dcaStr, vaStr, diffStr, diffColor;
                if (r.fmt === 'money') {
                    dcaStr = fmtMoney(r.dca); vaStr = fmtMoney(r.va);
                    const d = (r.va||0) - (r.dca||0); diffStr = fmtMoney(d, true); diffColor = colorCell(d);
                } else if (r.fmt === 'moneySigned') {
                    dcaStr = fmtMoney(r.dca, true); vaStr = fmtMoney(r.va, true);
                    const d = (r.va||0) - (r.dca||0); diffStr = fmtMoney(d, true); diffColor = colorCell(d);
                } else if (r.fmt === 'pct') {
                    dcaStr = fmtPct(r.dca); vaStr = fmtPct(r.va);
                    const d = (r.va||0) - (r.dca||0); diffStr = fmtPct(d); diffColor = colorCell(d);
                } else if (r.fmt === 'pctInverse') {
                    // 回撤：越小越好
                    dcaStr = (r.dca!=null?r.dca.toFixed(2):'-')+'%';
                    vaStr = (r.va!=null?r.va.toFixed(2):'-')+'%';
                    const d = (r.va||0) - (r.dca||0);
                    diffStr = (d>=0?'+':'')+d.toFixed(2)+'%';
                    diffColor = colorCell(d, 0, 'inverse');
                } else if (r.fmt === 'number') {
                    dcaStr = (r.dca!=null?Number(r.dca).toFixed(2):'-');
                    vaStr = (r.va!=null?Number(r.va).toFixed(2):'-');
                    const d = (r.va||0) - (r.dca||0);
                    diffStr = (d>=0?'+':'')+d.toFixed(2);
                    diffColor = colorCell(d);
                } else {
                    dcaStr = String(r.dca||'-'); vaStr = String(r.va||'-');
                    diffStr = ''; diffColor = '';
                }
                html += `<tr style="border-bottom:1px solid #eee;">`;
                html += `<td style="padding:8px 10px;">${r.label}</td>`;
                html += `<td style="padding:8px 10px;text-align:right;">${dcaStr}</td>`;
                html += `<td style="padding:8px 10px;text-align:right;">${vaStr}</td>`;
                html += `<td style="padding:8px 10px;text-align:right;${diffColor}">${diffStr}</td>`;
                html += `</tr>`;
            });
            html += '</table>';

            // 建议
            const diffPct = (va.total_return_pct||0) - (dca.total_return_pct||0);
            let suggestion = '';
            if (diffPct > 2) {
                suggestion = `<div class="alert alert-info" style="margin-top:15px;">
                    <strong>✅ VA 价值平均法领先 ${diffPct.toFixed(2)}%</strong><br>
                    在该区间内 VA 策略表现更优，自动"跌多买多、涨多卖出"带来超额收益。
                    <br>建议：若 ETF 池波动较大且能接受偶尔追加资金，可考虑切换到 VA。
                </div>`;
            } else if (diffPct < -2) {
                suggestion = `<div class="alert alert-info" style="margin-top:15px;">
                    <strong>✅ DCA 定投领先 ${(-diffPct).toFixed(2)}%</strong><br>
                    该区间市场更适合简单定投。
                    <br>建议：保持现有 DCA 策略。
                </div>`;
            } else {
                suggestion = `<div class="alert alert-info" style="margin-top:15px;">
                    两种策略效果接近（差异 ${diffPct.toFixed(2)}%）。DCA 更简单稳定，VA 更激进。
                </div>`;
            }
            html += suggestion;

            // 期末持仓明细
            if (data.holdings && data.holdings.length) {
                html += '<h3 style="margin-top:25px;">📋 期末持仓明细</h3>';
                html += '<table style="width:100%;border-collapse:collapse;font-size:13px;">';
                html += '<tr style="background:#95a5a6;color:white;">';
                html += '<th style="padding:8px;text-align:left;">策略</th>';
                html += '<th style="padding:8px;text-align:left;">代码</th>';
                html += '<th style="padding:8px;text-align:left;">名称</th>';
                html += '<th style="padding:8px;text-align:right;">持仓(股)</th>';
                html += '<th style="padding:8px;text-align:right;">市值</th>';
                html += '<th style="padding:8px;text-align:right;">成本</th>';
                html += '<th style="padding:8px;text-align:right;">收益率</th>';
                html += '</tr>';
                data.holdings.forEach(h => {
                    const profit = (h.market_value||0) - (h.total_cost||0);
                    const profitPct = h.total_cost > 0 ? (profit/h.total_cost*100) : 0;
                    html += `<tr style="border-bottom:1px solid #eee;">`;
                    html += `<td style="padding:6px 8px;">${h.strategy}</td>`;
                    html += `<td style="padding:6px 8px;">${h.code}</td>`;
                    html += `<td style="padding:6px 8px;">${h.name||''}</td>`;
                    html += `<td style="padding:6px 8px;text-align:right;">${h.shares||0}</td>`;
                    html += `<td style="padding:6px 8px;text-align:right;">${fmtMoney(h.market_value)}</td>`;
                    html += `<td style="padding:6px 8px;text-align:right;">${fmtMoney(h.total_cost)}</td>`;
                    html += `<td style="padding:6px 8px;text-align:right;${colorCell(profitPct)}">${fmtPct(profitPct)}</td>`;
                    html += `</tr>`;
                });
                html += '</table>';
            }

            document.getElementById('bt-results').innerHTML = html;
        }

        // 加载首页数据
        function loadHomeData() {
            fetch('/api/status')
                .then(r => r.json())
                .then(data => {
                    if (data.error) {
                        document.getElementById('current-month').textContent = '-';
                        document.getElementById('trading-days-count').textContent = '-';
                        document.getElementById('is-first-day').innerHTML = '<span class="status-warning">-</span>';
                        document.getElementById('total-invested').textContent = '-';
                        return;
                    }
                    document.getElementById('current-month').textContent = (data.year || '-') + '年' + (data.month || '-') + '月';
                    document.getElementById('trading-days-count').textContent = (data.total_trading_days || 0) + '天';
                    document.getElementById('is-first-day').innerHTML = data.is_first_day ?
                        '<span class="status-ok">是</span>' :
                        '<span class="status-warning">否</span>';
                    document.getElementById('total-invested').textContent = '¥' + (data.total_invested || 0).toFixed(2);

                    // 策略显示
                    var strategy = data.strategy || 'dca';
                    var strategyLabel = strategy === 'va'
                        ? '价值平均法 (VA)'
                        : '普通定投 (DCA)';
                    var strategyColor = strategy === 'va' ? '#e67e22' : '#3498db';
                    var strategyEl = document.getElementById('current-strategy');
                    if (strategyEl) {
                        strategyEl.innerHTML = '<span style="color:' + strategyColor + ';font-weight:bold;">' + strategyLabel + '</span>';
                    }

                    // 更新按钮文字
                    const toggleBtn = document.getElementById('btn-toggle-strategy');
                    if (toggleBtn) {
                        toggleBtn.textContent = strategy === 'va' ? '切换到 DCA' : '切换到 VA';
                        toggleBtn.title = strategy === 'va'
                            ? '切换到普通定投模式' : '切换到价值平均法模式';
                    }

                    // 更新执行按钮文字
                    const runBtn = document.getElementById('btn-run-dca');
                    if (runBtn) {
                        runBtn.textContent = strategy === 'va' ? '执行月度 VA' : '执行月度定投';
                    }
                })
                .catch(err => { console.error(err); });
        }

        // 切换策略
        function toggleStrategy() {
            const strategyEl = document.getElementById('current-strategy');
            const currentText = strategyEl ? strategyEl.textContent : '';
            const targetStrategy = currentText.includes('VA') ? 'dca' : 'va';
            const targetName = targetStrategy === 'va' ? '价值平均法 (VA)' : '普通定投 (DCA)';

            if (!confirm('确定要切换到' + targetName + '吗？\\n\\n切换后，下个月起将按新策略执行。')) return;

            fetch('/api/strategy/switch', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({strategy: targetStrategy})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    alert('已切换到 ' + data.strategy_name);
                    loadHomeData();
                } else {
                    alert('切换失败: ' + (data.error || '未知错误'));
                }
            })
            .catch(err => {
                alert('请求失败: ' + err);
            });
        }

        // 加载配置概览
        function loadConfigOverview() {
            fetch('/api/config')
                .then(r => r.json())
                .then(data => {
                    const container = document.getElementById('config-overview');
                    container.innerHTML = data.map(etf => `
                        <div class="config-item">
                            <div class="code">${etf.code}</div>
                            <div class="name">${etf.name}</div>
                            <div class="amount">¥${etf.monthly_amount}</div>
                            <div class="percent">${(etf.allocation * 100).toFixed(1)}%</div>
                        </div>
                    `).join('');
                });
        }

        // 加载系统参数
        function loadSystemParams() {
            fetch('/api/system-params')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('commission-rate').textContent = (data.commission_rate * 100).toFixed(3) + '%';
                    document.getElementById('min-commission').textContent = '¥' + data.min_commission.toFixed(2) + (data.min_commission > 0 ? ' (不足按' + data.min_commission.toFixed(0) + '元收)' : ' (无最低佣金)');
                    document.getElementById('min-shares').textContent = data.min_shares + '股';
                })
                .catch(err => console.error('Load system params failed:', err));
        }

        // 加载配置表格
        function loadConfigTable() {
            fetch('/api/config')
                .then(r => r.json())
                .then(data => {
                    const tbody = document.getElementById('config-table');
                    tbody.innerHTML = data.map(etf => `
                        <tr>
                            <td>${etf.code}</td>
                            <td>${etf.name}</td>
                            <td>${etf.category}</td>
                            <td>${(etf.allocation * 100).toFixed(1)}%</td>
                            <td>¥${etf.monthly_amount}</td>
                        </tr>
                    `).join('');

                    // 更新系统参数
                    const total = data.reduce((sum, etf) => sum + etf.monthly_amount, 0);
                    document.getElementById('total-amount').textContent = '¥' + total.toLocaleString();
                    document.getElementById('etf-count').textContent = data.length + '只';

                    // 加载系统参数
                    loadSystemParams();

                    // 更新编辑表格
                    const editTbody = document.getElementById('config-edit-table');
                    if (editTbody) {
                        editTbody.innerHTML = data.map((etf, idx) => `
                            <tr>
                                <td><input type="text" name="code" value="${etf.code}" style="width:80px"></td>
                                <td><input type="text" name="name" value="${etf.name}" style="width:100px"></td>
                                <td>
                                    <select name="category" style="width:70px">
                                        <option value="红利" ${etf.category=='红利'?'selected':''}>红利</option>
                                        <option value="宽基" ${etf.category=='宽基'?'selected':''}>宽基</option>
                                        <option value="行业" ${etf.category=='行业'?'selected':''}>行业</option>
                                        <option value="海外" ${etf.category=='海外'?'selected':''}>海外</option>
                                    </select>
                                </td>
                                <td><input type="number" name="allocation" value="${(etf.allocation * 100).toFixed(1)}" step="0.1" min="0" max="100" style="width:60px"></td>
                                <td><input type="number" name="monthly_amount" value="${etf.monthly_amount}" step="100" min="0" style="width:80px"></td>
                            </tr>
                        `).join('');
                    }
                });
        }

        // 切换编辑模式
        let originalConfig = null;
        function toggleEdit() {
            const form = document.getElementById('config-form');
            const viewTable = document.getElementById('config-view-table');
            if (form.style.display === 'none') {
                // 保存原始数据
                originalConfig = document.getElementById('config-edit-table').innerHTML;
                form.style.display = 'block';
                viewTable.style.display = 'none';
            } else {
                cancelEdit();
            }
        }

        // 取消编辑
        function cancelEdit() {
            document.getElementById('config-form').style.display = 'none';
            document.getElementById('config-view-table').style.display = 'block';
            loadConfigTable();
        }

        // 保存配置
        function saveConfig() {
            const rows = document.querySelectorAll('#config-edit-table tr');
            const config = [];
            rows.forEach(row => {
                const inputs = row.querySelectorAll('input, select');
                config.push({
                    code: inputs[0].value,
                    name: inputs[1].value,
                    category: inputs[2].value,
                    allocation: parseFloat(inputs[3].value) / 100,
                    monthly_amount: parseInt(inputs[4].value)
                });
            });

            fetch('/api/config/save', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(config)
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    alert('配置保存成功！');
                    cancelEdit();
                } else {
                    alert('保存失败: ' + data.message);
                }
            })
            .catch(err => alert('保存失败: ' + err));
        }

        // 系统参数编辑
        let originalSystemParams = null;
        function toggleSystemParamsEdit() {
            const form = document.getElementById('system-params-form');
            const view = document.getElementById('system-params-view');

            if (form.style.display === 'none') {
                // 保存原始值
                originalSystemParams = {
                    monthly_amount: document.getElementById('total-amount').textContent.replace(/[¥,]/g, ''),
                    commission_rate: (parseFloat(document.getElementById('commission-rate').textContent) * 100).toFixed(3),
                    min_commission: document.getElementById('min-commission').textContent.match(/[\\d.]+/)?.[0] || '5',
                    min_shares: document.getElementById('min-shares').textContent.match(/\\d+/)?.[0] || '100'
                };

                // 填充表单
                document.getElementById('edit-monthly-amount').value = originalSystemParams.monthly_amount;
                document.getElementById('edit-commission-rate').value = originalSystemParams.commission_rate;
                document.getElementById('edit-min-commission').value = originalSystemParams.min_commission;
                document.getElementById('edit-min-shares').value = originalSystemParams.min_shares;

                form.style.display = 'block';
                view.style.display = 'none';
            } else {
                cancelSystemParamsEdit();
            }
        }

        function cancelSystemParamsEdit() {
            document.getElementById('system-params-form').style.display = 'none';
            document.getElementById('system-params-view').style.display = 'grid';
        }

        function saveSystemParams() {
            const params = {
                monthly_amount: parseInt(document.getElementById('edit-monthly-amount').value),
                commission_rate: parseFloat(document.getElementById('edit-commission-rate').value) / 100,
                min_commission: parseFloat(document.getElementById('edit-min-commission').value),
                min_shares: parseInt(document.getElementById('edit-min-shares').value)
            };

            fetch('/api/system-params/save', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(params)
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    alert('系统参数保存成功！');
                    cancelSystemParamsEdit();
                    loadSystemParams(); // 刷新系统参数显示
                } else {
                    alert('保存失败: ' + data.message);
                }
            })
            .catch(err => alert('保存失败: ' + err));
        }

        // 加载持仓
        function loadPortfolio() {
            // 取消之前的请求
            if (portfolioCtrl) portfolioCtrl.abort();
            portfolioCtrl = new AbortController();

            // 每次调用都先显示loading（防止重复切换标签时旧数据残留）
            document.getElementById('portfolio-table').innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <p>加载中...</p>
                </div>
            `;

            fetch('/api/portfolio', {signal: portfolioCtrl.signal})
                .then(r => {
                    if (!r.ok) {
                        console.error('HTTP error:', r.status, r.statusText);
                        throw new Error('HTTP ' + r.status);
                    }
                    return r.json();
                })
                .then(data => {
                    console.log('Portfolio data received:', data);
                    
                    if (data.error) {
                        document.getElementById('portfolio-table').innerHTML =
                            '<p style="color:#dc3545;">加载失败: ' + data.error + '</p>';
                        return;
                    }

                    // 验证数据结构
                    if (!data.holdings || typeof data.total_invested !== 'number') {
                        console.error('Invalid data structure:', data);
                        document.getElementById('portfolio-table').innerHTML =
                            '<p style="color:#dc3545;">数据格式错误</p>';
                        return;
                    }

                    // 缓存数据用于编辑
                    portfolioData = data;

                    renderPortfolioTable(data);

                    // 更新统计（加 || 0 防止 undefined）
                    document.getElementById('stat-invested').textContent = '¥' + (Number(data.total_invested) || 0).toFixed(2);
                    document.getElementById('stat-value').textContent = '¥' + (Number(data.current_value) || 0).toFixed(2);
                    document.getElementById('stat-profit').textContent = '¥' + (Number(data.profit) || 0).toFixed(2);
                    document.getElementById('stat-return').textContent = (Number(data.return_rate) || 0).toFixed(2) + '%';
                    document.getElementById('stat-cash').textContent = '¥' + (Number(data.cash_balance) || 0).toFixed(2);
                    document.getElementById('stat-total').textContent = '¥' + ((Number(data.current_value) || 0) + (Number(data.cash_balance) || 0)).toFixed(2);
                })
                .catch(err => {
                    if (err.name === 'AbortError') return;  // 被取消的请求不显示错误
                    console.error('loadPortfolio failed:', err, err.stack);
                    document.getElementById('portfolio-table').innerHTML =
                        '<p style="color:#dc3545;">加载失败，请稍后重试</p>';
                });
        }

        // 渲染持仓表格
        function renderPortfolioTable(data, editMode = false) {
            const container = document.getElementById('portfolio-table');

            if (!data.holdings || data.holdings.length === 0) {
                container.innerHTML = '<p>暂无持仓</p>';
                return;
            }

            const tbody = document.createElement('tbody');
            data.holdings.forEach((h, idx) => {
                const tr = document.createElement('tr');
                if (editMode) tr.className = 'edit-row';
                tr.innerHTML = `
                    <td>${h.code}<input type="hidden" name="code" value="${h.code}"></td>
                    <td>${h.name}</td>
                    <td>${editMode
                        ? `<input type="number" class="edit-input" name="shares" value="${h.shares}" min="0" step="100">`
                        : h.shares}</td>
                    <td>${editMode
                        ? `<input type="number" class="edit-input" name="avg_cost" value="${h.avg_cost.toFixed(4)}" min="0" step="0.0001">`
                        : '¥' + h.avg_cost.toFixed(4)}</td>
                    <td>¥${h.current_value.toFixed(2)}</td>
                    <td class="${h.return >= 0 ? 'status-ok' : 'status-error'}">
                        ${h.return.toFixed(2)}%
                    </td>
                    <td class="action-cell">${editMode
                        ? `<button class="btn btn-warning btn-sm" onclick="resetHoldingRow(${idx})">重置</button>`
                        : ''}</td>
                `;
                tbody.appendChild(tr);
            });

            const table = document.createElement('table');
            table.innerHTML = `
                <thead>
                    <tr>
                        <th>代码</th>
                        <th>名称</th>
                        <th>股数</th>
                        <th>平均成本</th>
                        <th>当前市值</th>
                        <th>收益率</th>
                        <th></th>
                    </tr>
                </thead>
            `;
            table.appendChild(tbody);

            container.innerHTML = '';
            container.appendChild(table);
        }

        // 切换持仓编辑模式
        let originalPortfolioData = null;
        function togglePortfolioEdit() {
            if (!portfolioData) {
                alert('请先等待持仓数据加载完成');
                return;
            }

            const btnEdit = document.getElementById('btn-edit-portfolio');
            const btnSave = document.getElementById('btn-save-portfolio');
            const btnCancel = document.getElementById('btn-cancel-portfolio');

            if (btnEdit.textContent === '编辑') {
                // 进入编辑模式
                originalPortfolioData = JSON.parse(JSON.stringify(portfolioData));
                renderPortfolioTable(portfolioData, true);
                btnEdit.textContent = '完成';
                btnEdit.style.display = 'none';
                btnSave.style.display = 'inline-block';
                btnCancel.style.display = 'inline-block';
            } else {
                // 退出编辑模式
                cancelPortfolioEdit();
            }
        }

        // 重置单行数据
        function resetHoldingRow(idx) {
            if (!originalPortfolioData || !originalPortfolioData.holdings) return;
            const original = originalPortfolioData.holdings[idx];
            if (!original || !portfolioData.holdings) return;

            portfolioData.holdings[idx].shares = original.shares;
            portfolioData.holdings[idx].avg_cost = original.avg_cost;
            renderPortfolioTable(portfolioData, true);
        }

        // 取消编辑
        function cancelPortfolioEdit() {
            if (originalPortfolioData) {
                portfolioData = originalPortfolioData;
                originalPortfolioData = null;
            }

            const btnEdit = document.getElementById('btn-edit-portfolio');
            const btnSave = document.getElementById('btn-save-portfolio');
            const btnCancel = document.getElementById('btn-cancel-portfolio');

            btnEdit.textContent = '编辑';
            btnEdit.style.display = 'inline-block';
            btnSave.style.display = 'none';
            btnCancel.style.display = 'none';

            if (portfolioData) {
                renderPortfolioTable(portfolioData, false);
            }
        }

        // 保存持仓修改
        function savePortfolioChanges() {
            if (!portfolioData || !portfolioData.holdings) {
                alert('无持仓数据');
                return;
            }

            const rows = document.querySelectorAll('#portfolio-table tbody tr');
            const updates = [];

            rows.forEach((row, idx) => {
                const codeInput = row.querySelector('input[name="code"]');
                const sharesInput = row.querySelector('input[name="shares"]');
                const costInput = row.querySelector('input[name="avg_cost"]');

                if (codeInput && sharesInput && costInput) {
                    updates.push({
                        code: codeInput.value,
                        shares: parseInt(sharesInput.value) || 0,
                        avg_cost: parseFloat(costInput.value) || 0
                    });
                }
            });

            if (updates.length === 0) {
                alert('无有效数据');
                return;
            }

            if (!confirm(`确定要修改 ${updates.length} 条持仓数据吗？`)) return;

            fetch('/api/portfolio/update', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({updates: updates})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    alert('持仓数据已保存！');
                    originalPortfolioData = null;
                    document.getElementById('btn-edit-portfolio').textContent = '编辑';
                    document.getElementById('btn-edit-portfolio').style.display = 'inline-block';
                    document.getElementById('btn-save-portfolio').style.display = 'none';
                    document.getElementById('btn-cancel-portfolio').style.display = 'none';
                    loadPortfolio();  // 重新加载数据
                } else {
                    alert('保存失败: ' + data.message);
                }
            })
            .catch(err => alert('保存失败: ' + err));
        }

        // 标的检讨
        function loadReview() {
            document.getElementById('review-industry').innerHTML = '<div class="loading"><div class="spinner"></div><p>加载中...</p></div>';
            document.getElementById('review-balance').innerHTML = '<div class="loading"><div class="spinner"></div><p>加载中...</p></div>';

            fetch('/api/review')
                .then(r => r.json())
                .then(data => {
                    if (data.error) {
                        document.getElementById('review-industry').innerHTML = '<p style="color:#dc3545;">加载失败: ' + data.error + '</p>';
                        return;
                    }

                    // 行业ETF检讨
                    const industryHtml = data.industry.map(ind => `
                        <div class="review-item status-${ind.status}">
                            <div class="code-name">${ind.name} <small>${ind.code}</small></div>
                            <div class="numbers">
                                成本 ${ind.avg_cost ? '¥' + ind.avg_cost.toFixed(4) : '-'} |
                                现价 ${ind.current_price ? '¥' + ind.current_price.toFixed(4) : '-'}<br>
                                ${ind.return_pct !== undefined
                                    ? '<span style="color:' + (ind.return_pct >= 0 ? '#d32f2f' : '#2e7d32') + '">' + (ind.return_pct >= 0 ? '+' : '') + ind.return_pct.toFixed(2) + '%</span>'
                                    : ''}
                                持仓 ${ind.shares}股
                                <span class="review-status-badge ${ind.status}">${ind.status === 'danger' ? '注意' : ind.status === 'warn' ? '关注' : ind.status === 'good' ? '良好' : ind.status === 'empty' ? '空仓' : '正常'}</span>
                            </div>
                            <div class="suggestion">${ind.suggestion || ''}</div>
                        </div>
                    `).join('');
                    document.getElementById('review-industry').innerHTML = industryHtml;

                    // 类别平衡
                    const balanceHtml = data.balance.map(b => `
                        <div class="review-item status-${b.verdict === 'ok' ? 'ok' : (b.verdict === 'over' ? 'warn' : 'good')}">
                            <div class="code-name">${b.category} <small style="font-weight:normal;color:#999;">${b.target_pct}%</small></div>
                            <div class="numbers">
                                实际 ${b.actual_pct}%
                                <span style="color:${b.deviation > 0 ? '#d32f2f' : b.deviation < 0 ? '#2e7d32' : '#666'};font-weight:bold;">
                                    (${b.deviation > 0 ? '+' : ''}${b.deviation}%)
                                </span>
                            </div>
                            <div class="suggestion">${b.suggestion}</div>
                        </div>
                    `).join('');
                    document.getElementById('review-balance').innerHTML = balanceHtml;

                    // 总结
                    const summaryEl = document.getElementById('review-summary');
                    summaryEl.textContent = data.summary;
                    summaryEl.className = 'alert ' + (data.summary.startsWith('✅') ? 'alert-success' : 'alert-warning');
                })
                .catch(err => {
                    document.getElementById('review-industry').innerHTML = '<p style="color:#dc3545;">加载失败，请稍后重试</p>';
                    console.error('loadReview failed:', err);
                });
        }

        // 加载历史
        function loadHistory() {
            fetch('/api/history')
                .then(r => r.json())
                .then(data => {
                    if (data.length > 0) {
                        document.getElementById('history-list').innerHTML = data.slice().reverse().map(trade => {
                            const datePart = trade.timestamp || trade.date;
                            const tradeType = trade.type || 'other';
                            let typeLabel = '其他';
                            let typeColor = '#999';
                            let typeBg = '#f5f5f5';
                            if (tradeType === 'dca') { typeLabel = '定投'; typeColor = '#3498db'; typeBg = '#e8f4fc'; }
                            else if (tradeType === 'stop_profit') { typeLabel = '止盈'; typeColor = '#e74c3c'; typeBg = '#fdecea'; }
                            else if (tradeType === 'reinvest') { typeLabel = '再投'; typeColor = '#27ae60'; typeBg = '#ecfdf5'; }
                            return `
                            <div class="history-item">
                                <div class="date">${datePart}</div>
                                <div class="details">
                                    <span style="display:inline-block;padding:2px 8px;border-radius:12px;background:${typeBg};color:${typeColor};font-size:12px;font-weight:bold;margin-right:8px;">${typeLabel}</span>
                                    <span style="color:#333;font-weight:500;">${trade.code}</span>
                                    <span style="color:#666;margin:0 8px;">${trade.name}</span>
                                    <span style="color:#888;">| 价:¥${trade.price.toFixed(4)}</span>
                                    <span style="color:#888;margin-left:10px;">| 股:${trade.shares}</span>
                                    <span style="color:#888;margin-left:10px;">| 额:¥${trade.trade_amount.toFixed(2)}</span>
                                </div>
                            </div>
                            `;
                        }).join('');
                    } else {
                        document.getElementById('history-list').innerHTML = '<p style="color:#888;font-size:0.9em;">暂无交易记录</p>';
                    }
                });
        }

        // 加载日历
        function loadCalendar() {
            fetch('/api/calendar')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('first-trading-day').textContent = data.first_trading_day || '-';
                    document.getElementById('last-trading-day').textContent = data.last_trading_day || '-';
                    document.getElementById('total-trading-days').textContent = data.total_trading_days || '-';
                    document.getElementById('today-date').textContent = data.today || '-';

                    const grid = document.getElementById('calendar-grid');
                    grid.innerHTML = '';

                    const days = ['日', '一', '二', '三', '四', '五', '六'];
                    for (let i = 1; i <= 31; i++) {
                        const dateStr = data.year + '-' +
                            String(data.month).padStart(2, '0') + '-' +
                            String(i).padStart(2, '0');

                        const isTrading = data.trading_days.includes(dateStr);
                        const isFirst = dateStr === data.first_trading_day;
                        const isToday = dateStr === data.today;

                        if (isTrading || isToday) {
                            const div = document.createElement('div');
                            div.className = 'calendar-day';
                            if (isTrading) div.className += ' trading';
                            if (isFirst) div.className += ' first';
                            if (isToday) div.className += ' today';
                            div.innerHTML = `<div>${i}</div><div style="font-size:0.8em">${days[new Date(dateStr).getDay()]}</div>`;
                            grid.appendChild(div);
                        }
                    }
                });
        }

        // 执行定投
        function runDCA() {
            if (!confirm('确定要执行月度定投吗？')) return;

            const btn = event.target;
            btn.disabled = true;
            btn.textContent = '执行中...';

            fetch('/api/dca', {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        alert('定投执行成功！\\n总投入: ¥' + data.total_invested.toFixed(2));
                    } else {
                        alert('定投未执行: ' + data.message);
                    }
                    loadHomeData();
                    loadPortfolio();
                    loadHistory();
                })
                .finally(() => {
                    btn.disabled = false;
                    btn.textContent = '执行月度定投';
                });
        }

        // 查看持仓
        function checkPortfolio() {
            showSection('portfolio');
        }

        // 导出数据
        function exportData() {
            window.location.href = '/api/export';
        }

        // 刷新数据
        function refreshData() {
            loadHomeData();
            alert('数据已刷新');
        }

        // 运行诊断
        function runDiagnose() {
            const btn = event.target;
            btn.disabled = true;
            btn.textContent = '诊断中...';

            fetch('/api/diagnose')
                .then(r => r.json())
                .then(data => {
                    let html = '<div class="alert alert-success"><strong>诊断结果</strong></div>';
                    html += '<table><thead><tr><th>项目</th><th>状态</th></tr></thead><tbody>';

                    Object.entries(data).forEach(([key, value]) => {
                        const status = value === 'OK' || value === true ?
                            '<span class="status-ok">✓ 正常</span>' :
                            '<span class="status-error">✗ ' + value + '</span>';
                        html += `<tr><td>${key}</td><td>${status}</td></tr>`;
                    });

                    html += '</tbody></table>';
                    document.getElementById('diagnose-results').innerHTML = html;
                })
                .finally(() => {
                    btn.disabled = false;
                    btn.textContent = '运行诊断';
                });
        }

        // 页面加载时
        document.addEventListener('DOMContentLoaded', function() {
            loadHomeData();
            loadConfigTable();

            // 每30秒自动刷新首页数据
            setInterval(loadHomeData, 30000);
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """首页"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def get_status():
    """获取系统状态"""
    from datetime import datetime

    try:
        from dca_calendar import get_current_month_info
        month_info = get_current_month_info()
    except Exception as e:
        print(f"Calendar error: {e}")
        month_info = {
            'year': datetime.now().year,
            'month': datetime.now().month,
            'total_trading_days': 0,
            'first_trading_day': None,
            'is_first_day': False,
            'today': datetime.now().strftime('%Y-%m-%d')
        }

    try:
        from dca_portfolio_manager import PortfolioManager
        pm = PortfolioManager()
        total_invested = pm.total_invested if hasattr(pm, 'total_invested') else 0
        strategy = getattr(pm, 'strategy', 'dca')
    except Exception as e:
        print(f"Portfolio error: {e}")
        total_invested = 0
        strategy = 'dca'

    return jsonify({
        'year': month_info.get('year', datetime.now().year),
        'month': month_info.get('month', datetime.now().month),
        'total_trading_days': month_info.get('total_trading_days', 0),
        'first_trading_day': month_info.get('first_trading_day'),
        'is_first_day': month_info.get('is_first_day', False),
        'today': month_info.get('today', datetime.now().strftime('%Y-%m-%d')),
        'total_invested': total_invested,
        'strategy': strategy,
    })


@app.route('/api/strategy/switch', methods=['POST'])
def switch_strategy():
    """切换策略 (dca / va)"""
    try:
        data = request.get_json() or {}
        strategy = data.get('strategy', 'dca')

        if strategy not in ('dca', 'va'):
            return jsonify({'success': False, 'error': '无效策略类型'}), 400

        from dca_portfolio_manager import PortfolioManager
        pm = PortfolioManager()
        pm.strategy = strategy
        pm.save_data()

        strategy_name = '价值平均法 (VA)' if strategy == 'va' else '普通定投 (DCA)'
        print(f"[策略切换] 已切换为: {strategy_name}")

        return jsonify({
            'success': True,
            'strategy': strategy,
            'strategy_name': strategy_name,
        })
    except Exception as e:
        import traceback
        print(f"[策略切换] 异常: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system-params')
def get_system_params():
    """获取系统参数"""
    try:
        from dca_config import DCA_CONFIG
        return jsonify(DCA_CONFIG)
    except Exception as e:
        return jsonify({
            'monthly_amount': 3000,
            'commission_rate': 0.0001,
            'min_commission': 5.0,
            'min_shares': 100
        })

@app.route('/api/config')
def get_config():
    """获取配置"""
    try:
        from dca_config import ETF_PORTFOLIO
        return jsonify(ETF_PORTFOLIO)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config/save', methods=['POST'])
def save_config():
    """保存ETF配置"""
    try:
        from flask import request
        import os

        config = request.json

        # 读取现有配置
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dca_config.py')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                existing = f.read()
            # 提取DCA_CONFIG部分
            import re
            dca_match = re.search(r"(# 定投方案基本配置\nDCA_CONFIG\s*=\s*\{[^}]+\})", existing, re.DOTALL)
            if dca_match:
                dca_part = dca_match.group(1)
            else:
                dca_part = """# 定投方案基本配置
DCA_CONFIG = {
    'monthly_amount': 3000,
    'commission_rate': 0.0001,
    'min_commission': 5.0,
    'min_shares': 100,
    'description': '平衡型定投方案 - 适合大多数年轻人'
}"""
        except:
            dca_part = """# 定投方案基本配置
DCA_CONFIG = {
    'monthly_amount': 3000,
    'commission_rate': 0.0001,
    'min_commission': 5.0,
    'min_shares': 100,
    'description': '平衡型定投方案 - 适合大多数年轻人'
}"""

        # 生成ETF配置列表的Python代码
        etf_lines = []
        for etf in config:
            etf_lines.append("    {")
            etf_lines.append(f"        'code': '{etf['code']}',")
            etf_lines.append(f"        'name': '{etf['name']}',")
            etf_lines.append(f"        'category': '{etf['category']}',")
            etf_lines.append(f"        'allocation': {etf['allocation']},")
            etf_lines.append(f"        'monthly_amount': {etf['monthly_amount']},")
            etf_lines.append("    },")
        etf_config = "[\n" + "\n".join(etf_lines) + "\n]"

        content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定投组合配置
方案2：平衡型（适合大多数年轻人）
- 红利ETF：20%（515080）
- 宽基指数：40%（510300沪深300+510500中证500）
- 行业主题：25%（512760芯片+512010医药）
- 海外资产：15%（513100纳指）
"""

''' + dca_part + '''

# ETF配置列表
ETF_PORTFOLIO = ''' + etf_config + '''
'''

        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return jsonify({'success': True, 'message': 'ETF配置已保存'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/system-params/save', methods=['POST'])
def save_system_params():
    """保存系统参数"""
    try:
        from flask import request
        import os
        import re

        params = request.json

        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dca_config.py')

        # 读取现有配置
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            content = ''

        # 提取ETF_PORTFOLIO部分
        etf_match = re.search(r'(# ETF配置列表\nETF_PORTFOLIO\s*=\s*\[.*?\])', content, re.DOTALL)
        etf_part = etf_match.group(1) if etf_match else '# ETF配置列表\nETF_PORTFOLIO = []'

        # 生成新的DCA_CONFIG（确保commission_rate格式正确）
        commission_rate = params.get('commission_rate', 0.0001)
        # 如果值大于1，说明传的是百分数，需要转换
        if commission_rate > 1:
            commission_rate = commission_rate / 100

        new_dca = f"""# 定投方案基本配置
DCA_CONFIG = {{
    'monthly_amount': {params.get('monthly_amount', 3000)},
    'commission_rate': {commission_rate},
    'min_commission': {params.get('min_commission', 5.0)},
    'min_shares': {params.get('min_shares', 100)},
    'description': '平衡型定投方案 - 适合大多数年轻人'
}}"""

        # 生成完整配置
        full_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定投组合配置
方案2：平衡型（适合大多数年轻人）
"""

{new_dca}

{etf_part}
'''

        # 保存
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(full_content)

        return jsonify({'success': True, 'message': '系统参数已保存'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

# 价格缓存，5分钟有效期
_price_cache = {}
_price_cache_time = 0

@app.route('/api/portfolio')
def get_portfolio():
    """获取持仓"""
    global _price_cache, _price_cache_time
    
    try:
        from dca_trading import get_etf_price
        from dca_portfolio_manager import PortfolioManager
        from dca_config import ETF_PORTFOLIO
        import time

        print("[API] 获取持仓数据")
        
        pm = PortfolioManager()
        now = time.time()

        # 获取当前价格（使用缓存，5分钟刷新一次）
        if now - _price_cache_time > 300:  # 超过5分钟刷新
            _price_cache = {}
            from dca_data_sources import get_realtime_prices_batch

            # 优先 mootdx 批量接口（一次调用拿全部，~0.06s）
            all_codes = [etf['code'] for etf in ETF_PORTFOLIO]
            try:
                batch_prices = get_realtime_prices_batch(all_codes)
            except Exception as e:
                print(f"[API] mootdx 批量获取异常: {e}")
                batch_prices = {}

            for code, info in batch_prices.items():
                _price_cache[code] = info['price']
                print(f"[API] mootdx 获取 {code} 价格: {info['price']}")

            # mootdx 未拿到的，用 HTTP 兜底链（并发，总超时12秒）
            missing_codes = [c for c in all_codes if c not in _price_cache]
            if missing_codes:
                print(f"[API] mootdx 缺失 {len(missing_codes)} 只，走 HTTP 兜底: {missing_codes}")
                from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeout

                def _fetch_one(etf_code):
                    try:
                        return etf_code, get_etf_price(etf_code)
                    except Exception as e:
                        return etf_code, {'success': False, 'error': str(e)}

                with ThreadPoolExecutor(max_workers=max(4, len(missing_codes))) as executor:
                    futures = [executor.submit(_fetch_one, c) for c in missing_codes]
                    try:
                        for fut in as_completed(futures, timeout=12):
                            etf_code, info = fut.result()
                            if info.get('success'):
                                _price_cache[etf_code] = info['price']
                                print(f"[API] HTTP 获取 {etf_code} 价格: {info['price']}")
                            else:
                                print(f"[API] HTTP 获取 {etf_code} 价格失败: {info.get('error', '未知错误')}")
                    except FuturesTimeout:
                        print("[API] HTTP 兜底部分超时（12秒），未拿到的用成本价兜底")

            _price_cache_time = now
            print(f"[API] 价格缓存更新完成，缓存 {len(_price_cache)} 个价格")
        else:
            print(f"[API] 使用缓存价格，缓存 {len(_price_cache)} 个价格")
        
        prices = _price_cache

        # 计算收益
        holdings_data = []
        total_invested = float(pm.total_invested) if pm.total_invested else 0
        current_value = 0

        for code, holding in pm.holdings.items():
            if holding['shares'] > 0:
                price = prices.get(code, holding['avg_cost'])
                value = holding['shares'] * price
                current_value += value

                total_cost = float(holding['total_cost']) if holding['total_cost'] else 0
                return_rate = ((value - total_cost) / total_cost * 100) if total_cost > 0 else 0

                holdings_data.append({
                    'code': code,
                    'name': holding['name'],
                    'shares': int(holding['shares']),
                    'avg_cost': float(holding['avg_cost']),
                    'current_price': float(price),
                    'current_value': float(value),
                    'return': float(return_rate)
                })

        profit = float(current_value - total_invested)
        return_rate = (profit / total_invested * 100) if total_invested > 0 else 0

        result = {
            'holdings': holdings_data,
            'total_invested': float(total_invested),
            'current_value': float(current_value),
            'profit': float(profit),
            'return_rate': float(return_rate),
            'cash_balance': float(pm.cash_balance)
        }
        
        print(f"[API] 返回持仓数据: {len(holdings_data)} 个持仓, 总投入: {total_invested}, 当前市值: {current_value}")
        
        return jsonify(result)
        
    except Exception as e:
        error_msg = f"获取持仓失败: {str(e)}"
        print(f"[API ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': error_msg}), 500

@app.route('/api/portfolio/update', methods=['POST'])
def update_portfolio():
    """更新持仓数据（手动调整）"""
    try:
        from flask import request
        from dca_portfolio_manager import PortfolioManager
        from datetime import datetime

        data = request.json
        updates = data.get('updates', [])

        if not updates:
            return jsonify({'success': False, 'message': '无更新数据'}), 400

        pm = PortfolioManager()
        updated_count = 0

        for update in updates:
            code = update.get('code')
            shares = update.get('shares', 0)
            avg_cost = update.get('avg_cost', 0)

            if code not in pm.holdings:
                continue

            old_shares = pm.holdings[code]['shares']
            old_cost = pm.holdings[code]['total_cost']

            # 更新持仓
            pm.holdings[code]['shares'] = shares
            pm.holdings[code]['avg_cost'] = avg_cost

            # 重新计算总成本
            if shares > 0:
                pm.holdings[code]['total_cost'] = round(shares * avg_cost, 2)
            else:
                pm.holdings[code]['total_cost'] = 0
                pm.holdings[code]['avg_cost'] = 0

            new_cost = pm.holdings[code]['total_cost']

            # 调整总投入金额
            if old_cost != new_cost:
                pm.total_invested += (new_cost - old_cost)

            # 添加调整记录到交易历史
            if old_shares != shares or old_cost != new_cost:
                pm.trade_history.append({
                    'success': True,
                    'code': code,
                    'name': pm.holdings[code].get('name', ''),
                    'price': avg_cost,
                    'shares': shares - old_shares,
                    'trade_amount': round((shares - old_shares) * avg_cost, 2) if shares > old_shares else 0,
                    'commission': 0,
                    'total_cost': new_cost,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'note': '手动调整持仓',
                    'adjustment': True
                })

            updated_count += 1

        # 保存数据
        pm.save_data()

        return jsonify({
            'success': True,
            'message': f'已更新 {updated_count} 条持仓数据',
            'updated_count': updated_count
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/history')
def get_history():
    """获取交易历史"""
    try:
        from dca_portfolio_manager import PortfolioManager
        pm = PortfolioManager()
        return jsonify(pm.trade_history)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/review')
def get_review():
    """获取标的物检讨报告"""
    try:
        from dca_portfolio_manager import PortfolioManager
        from dca_trading import get_etf_price
        from dca_config import ETF_PORTFOLIO
        from dca_review import run_full_review
        pm = PortfolioManager()
        prices = {}
        for etf in ETF_PORTFOLIO:
            info = get_etf_price(etf['code'])
            if info['success']:
                prices[etf['code']] = info['price']
        review = run_full_review(pm, prices)
        return jsonify(review)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/calendar')
def get_calendar():
    """获取日历信息"""
    try:
        from dca_calendar import get_current_month_info
        info = get_current_month_info()
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dca', methods=['POST'])
def execute_dca():
    """执行定投"""
    try:
        from dca_main import DCASystem

        dca = DCASystem()
        result = dca.run_dca_cycle()

        if result['success']:
            total_invested = sum(t['total_cost'] for t in result['trades'])
            return jsonify({
                'success': True,
                'message': '定投成功',
                'trades': result['trades'],
                'total_invested': total_invested
            })
        else:
            return jsonify({
                'success': False,
                'message': result.get('message', '未知错误')
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/export')
def export_data():
    """导出数据"""
    try:
        from dca_portfolio_manager import PortfolioManager
        pm = PortfolioManager()
        filename = pm.export_to_csv('dca_trade_history.csv')
        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/diagnose')
def diagnose():
    """系统诊断"""
    results = {}

    # 检查Python版本
    results['Python版本'] = 'OK' if sys.version_info >= (3, 6) else '需要Python 3.6+'

    # 检查文件
    import os
    required_files = [
        'dca_config.py',
        'dca_calendar.py',
        'dca_trading.py',
        'dca_portfolio_manager.py',
        'dca_main.py'
    ]

    for f in required_files:
        results[f] = 'OK' if os.path.exists(f) else '缺失'

    # 检查依赖
    dependencies = {
        'pandas': 'pandas',
        'akshare': 'akshare',
        'docx': 'python-docx',
        'schedule': 'schedule'
    }

    for lib_name, pkg_name in dependencies.items():
        try:
            __import__(lib_name)
            results[pkg_name] = 'OK'
        except ImportError:
            results[pkg_name] = '未安装'

    return jsonify(results)


# ════════════════════════════════════════════
# 通达信行情桥接 API
# ════════════════════════════════════════════

@app.route("/api/tdx/push", methods=["POST"])
def tdx_push_quotes():
    """接收通达信MCP行情数据并写入缓存"""
    try:
        data = request.get_json(force=True)
        if not data or not isinstance(data, dict):
            return jsonify({"ok": False, "msg": "无效的数据格式"}), 400
        from pathlib import Path
        import json as _json, time as _time
        _cache_file = Path(__file__).parent / "data" / "tdx_cache.json"
        _cache_file.parent.mkdir(parents=True, exist_ok=True)
        now = _time.time()
        cache = {}
        if _cache_file.exists():
            try:
                with open(_cache_file, "r", encoding="utf-8") as f:
                    cache = _json.load(f)
            except Exception:
                cache = {}
        for code, entry in data.items():
            cache[str(code)] = {
                "price": entry.get("price", 0),
                "close": entry.get("close", 0),
                "time": now,
            }
        with open(_cache_file, "w", encoding="utf-8") as f:
            _json.dump(cache, f, ensure_ascii=False, indent=2)
        return jsonify({"ok": True, "count": len(data)})
    except Exception as e:
        print(f"[通达信] API推送失败: {e}")
        return jsonify({"ok": False, "msg": str(e)}), 500


@app.route("/api/tdx/status")
def tdx_status():
    """查看通达信缓存状态"""
    from pathlib import Path
    import json as _json, time as _time
    _cache_file = Path(__file__).parent / "data" / "tdx_cache.json"
    if not _cache_file.exists():
        return jsonify({"ok": True, "cached_codes": 0, "status": "无缓存数据"})
    try:
        with open(_cache_file, "r", encoding="utf-8") as f:
            cache = _json.load(f)
        now = _time.time()
        codes_info = {}
        fresh_count = 0
        for code, entry in cache.items():
            age = now - entry.get("time", 0)
            is_fresh = age < 120
            if is_fresh:
                fresh_count += 1
            codes_info[code] = {
                "price": entry.get("price"),
                "age_seconds": int(age),
                "fresh": is_fresh
            }
        return jsonify({"ok": True, "cached_codes": len(cache), "fresh_codes": fresh_count, "codes": codes_info})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500


def open_browser():
    """延迟打开浏览器（检测端口就绪后立即打开）"""
    import socket
    import time
    url = f"http://127.0.0.1:{DCA_WEB_PORT}"
    # 检测Flask端口是否就绪，最多等2秒
    for _ in range(20):
        try:
            with socket.create_connection(("127.0.0.1", DCA_WEB_PORT), timeout=0.1):
                break
        except (socket.timeout, ConnectionRefusedError, OSError):
            time.sleep(0.1)
    print(f"\n  自动打开浏览器: {url}")
    webbrowser.open(url)


DCA_WEB_PORT = 8080


def _warmup_mootdx():
    """后台预热 mootdx 客户端（避免首次持仓加载等4-5秒选服务器）"""
    try:
        from dca_data_sources import _get_mootdx_client
        client = _get_mootdx_client()
        if client is not None:
            print("[warmup] mootdx 客户端已就绪")
        else:
            print("[warmup] mootdx 客户端创建失败，将走兜底链")
    except Exception as e:
        print(f"[warmup] mootdx 预热异常: {e}")


@app.route('/api/backtest/compare', methods=['POST'])
def api_backtest_compare():
    """回测对比 DCA vs VA"""
    try:
        from datetime import datetime
        data = request.get_json() or {}
        start = data.get('start', '2024-06-01')
        end = data.get('end', datetime.now().strftime('%Y-%m-%d'))
        amount = float(data.get('amount', 3000))
        threshold = float(data.get('threshold', 0.20))

        print(f"[回测API] 开始: {start} ~ {end}, 月投¥{amount}, 止盈{threshold*100:.0f}%")

        # 懒加载 dca_backtest（避免启动时加载 numpy）
        from dca_backtest import simulate_monthly_dca, simulate_value_averaging, ETF_NAMES

        # 从 dca_config 读取 allocation
        from dca_config import ETF_PORTFOLIO
        allocation = {etf['code']: etf.get('monthly_amount', 500) for etf in ETF_PORTFOLIO}
        # 归一化为比例
        total_alloc = sum(allocation.values()) or 1
        allocation = {k: v/total_alloc for k, v in allocation.items()}

        config = {
            'monthly_amount': amount,
            'commission_rate': 0.0001,
            'stop_profit_threshold': threshold,
            'allocation': allocation,
        }

        print("[回测API] 正在跑 DCA...")
        dca_result = simulate_monthly_dca(config, start, end)
        print("[回测API] 正在跑 VA...")
        va_result = simulate_value_averaging(config, start, end)

        if 'error' in dca_result or 'error' in va_result:
            return jsonify({
                'error': dca_result.get('error', '') or va_result.get('error', '')
            })

        # 构造期末持仓明细（用于前端表格展示）
        holdings_list = []
        # DCA 持仓
        for code in allocation.keys():
            h = dca_result.get('holdings', {}).get(code, {})
            if h.get('shares', 0) > 0:
                holdings_list.append({
                    'strategy': 'DCA',
                    'code': code,
                    'name': ETF_NAMES.get(code, ''),
                    'shares': h['shares'],
                    'avg_cost': round(h.get('avg_cost', 0), 4),
                    'total_cost': round(h.get('total_cost', 0), 2),
                    'market_value': round(h.get('market_value', h.get('total_cost', 0)), 2),
                })
        for code in allocation.keys():
            h = va_result.get('holdings', {}).get(code, {})
            if h.get('shares', 0) > 0:
                holdings_list.append({
                    'strategy': 'VA',
                    'code': code,
                    'name': ETF_NAMES.get(code, ''),
                    'shares': h['shares'],
                    'avg_cost': round(h.get('avg_cost', 0), 4),
                    'total_cost': round(h.get('total_cost', 0), 2),
                    'market_value': round(h.get('market_value', h.get('total_cost', 0)), 2),
                })

        return jsonify({
            'start_date': start,
            'end_date': end,
            'amount': amount,
            'threshold': threshold,
            'dca': dca_result,
            'va': va_result,
            'holdings': holdings_list,
        })
    except Exception as e:
        import traceback
        print(f"[回测API] 异常: {e}")
        traceback.print_exc()
        return jsonify({'error': f'回测失败: {str(e)}'})


def run(auto_open=True):
    """运行服务器"""
    print("\n" + "=" * 70)
    print("平衡型定投系统 Web版 v1.1")
    print("=" * 70)
    print(f"\nWeb server starting at: http://127.0.0.1:{DCA_WEB_PORT}")

    # 后台预热 mootdx 客户端（与 Flask 启动并行）
    threading.Thread(target=_warmup_mootdx, daemon=True).start()

    if auto_open:
        t = threading.Thread(target=open_browser, daemon=True)
        t.start()

    app.run(host='0.0.0.0', port=DCA_WEB_PORT, debug=False)


@app.route('/stop_profit')
def stop_profit_page():
    """止盈轮动页面"""
    return render_template_string(STOP_PROFIT_HTML)


@app.route('/api/stop_profit/status')
def stop_profit_status():
    """获取止盈轮动状态（读价格缓存，不再实时调行情）"""
    try:
        print("[止盈轮动API] 开始获取状态")
        from dca_price_cache import get_all_cached_prices, refresh_prices
        from dca_portfolio_manager import PortfolioManager
        from dca_config import ETF_PORTFOLIO
        
        print("[止盈轮动API] 初始化持仓管理器")
        pm = PortfolioManager()
        
        if not pm.holdings:
            print("[止盈轮动API] 警告：持仓数据为空")
        
        # 读价格缓存（不调实时行情）
        prices = get_all_cached_prices()
        if not prices:
            # 无当天缓存，自动刷新一次
            print("[止盈轮动API] 价格缓存为空，自动刷新...")
            refresh_prices()
            prices = get_all_cached_prices()
        print(f"[止盈轮动API] 缓存价格 {len(prices)} 个ETF")
        
        # 计算类别配比（使用成本价作为备选）
        total_value = 0
        cat_values = {}
        for code, holding in pm.holdings.items():
            if holding['shares'] > 0:
                # 读缓存价格，失败时用成本价兜底
                current_price = prices.get(code, holding['avg_cost'])
                value = holding['shares'] * current_price
                total_value += value
                cat = holding.get('category', '其他')
                cat_values[cat] = cat_values.get(cat, 0) + value
        
        cat_alloc = {}
        target_alloc = {'红利': 0.20, '宽基': 0.40, '行业': 0.25, '海外': 0.15}
        for cat, target in target_alloc.items():
            current = cat_values.get(cat, 0) / total_value if total_value > 0 else 0
            cat_alloc[cat] = {
                'current_pct': round(current * 100, 2),
                'target_pct': round(target * 100, 2),
                'deviation': round((current - target) * 100, 2)
            }

        # 每个ETF的盈亏和阈值（使用成本价作为备选）
        holdings_info = []
        for code, holding in pm.holdings.items():
            if holding['shares'] > 0:
                # 读缓存价格，失败时用成本价兜底
                current_price = prices.get(code, holding['avg_cost'])
                avg_cost = holding['avg_cost']
                profit_pct = (current_price - avg_cost) / avg_cost * 100 if avg_cost > 0 else 0
                distance_to_threshold = STOP_PROFIT_CONFIG_WEB.get('threshold', 0.20) * 100 - profit_pct
                holdings_info.append({
                    'code': code,
                    'name': holding.get('name', code),
                    'shares': holding['shares'],
                    'avg_cost': round(avg_cost, 4),
                    'current_price': round(current_price, 4),
                    'profit_pct': round(profit_pct, 2),
                    'distance': round(distance_to_threshold, 2),
                    'need_gain': round(avg_cost * 1.20, 4) if avg_cost > 0 else 0,
                    'price_source': 'cache' if code in prices else 'cost'
                })

        return jsonify({
            'signals': [],
            'holdings_info': holdings_info,
            'category_allocation': cat_alloc,
            'frozen_etfs': [],
            'history': [],
            'price_status': 'partial_cache' if len(prices) > 0 and len(prices) < len(pm.holdings) else ('full_cache' if len(prices) == len(pm.holdings) else 'cache_empty')
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/stop_profit/execute', methods=['POST'])
def execute_stop_profit_api():
    """执行止盈轮动"""
    try:
        from dca_portfolio_manager import PortfolioManager
        from dca_stop_profit import StopProfitManager
        pm = PortfolioManager()
        spm = StopProfitManager(pm)
        result = spm.run_daily_check()
        spm.generate_html_report(result)
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


# 止盈轮动阈值配置（从dca_stop_profit读取）
try:
    from dca_stop_profit import STOP_PROFIT_CONFIG as _sp_config
    STOP_PROFIT_CONFIG_WEB = _sp_config
except ImportError:
    STOP_PROFIT_CONFIG_WEB = {'threshold': 0.20, 'freeze_days': 30}


# 止盈轮动页面HTML
STOP_PROFIT_HTML = r"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>止盈轮动追踪 - 定投系统</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Microsoft YaHei', Arial; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); min-height: 100vh; padding: 20px; color: #e0e0e0; }
        .container { max-width: 1100px; margin: 0 auto; }
        .header { text-align: center; padding: 30px; background: linear-gradient(135deg, #e74c3c, #c0392b); border-radius: 16px; margin-bottom: 20px; }
        .header h1 { font-size: 32px; color: white; }
        .header p { color: rgba(255,255,255,0.8); margin-top: 8px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; margin-bottom: 20px; }
        .card { background: #1e2a3a; border-radius: 12px; padding: 20px; border: 1px solid #2a3a4a; }
        .card h2 { font-size: 18px; color: #3498db; margin-bottom: 12px; border-bottom: 1px solid #2a3a4a; padding-bottom: 8px; }
        .etf-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #2a3a4a; }
        .etf-row:last-child { border-bottom: none; }
        .etf-name { font-weight: bold; }
        .etf-profit { font-size: 16px; }
        .positive { color: #e74c3c; }
        .negative { color: #2ecc71; }
        .progress-bar { height: 8px; background: #2a3a4a; border-radius: 4px; margin-top: 4px; overflow: hidden; }
        .progress-fill { height: 100%; border-radius: 4px; transition: width 0.5s; }
        .progress-positive { background: linear-gradient(90deg, #f39c12, #e74c3c); }
        .progress-negative { background: linear-gradient(90deg, #2ecc71, #27ae60); }
        .trigger-line { position: relative; }
        .trigger-mark { position: absolute; top: -2px; width: 3px; height: 12px; background: #e74c3c; border-radius: 2px; }
        .category-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
        .cat-item { text-align: center; padding: 12px; background: #253545; border-radius: 8px; }
        .cat-name { font-size: 13px; color: #7f8c8d; }
        .cat-pct { font-size: 20px; font-weight: bold; }
        .cat-deviation { font-size: 12px; margin-top: 4px; }
        .under { color: #2ecc71; }
        .over { color: #e74c3c; }
        .balanced { color: #f39c12; }
        .btn { padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: bold; }
        .btn-danger { background: #e74c3c; color: white; }
        .btn-primary { background: #3498db; color: white; }
        .btn:hover { opacity: 0.85; }
        .actions { display: flex; gap: 12px; margin-bottom: 20px; }
        .refresh-time { text-align: right; color: #7f8c8d; font-size: 12px; margin-bottom: 12px; }
        .signal-alert { background: #2c1a1a; border: 1px solid #e74c3c; border-radius: 8px; padding: 12px; margin-bottom: 12px; }
        .signal-alert .code { font-size: 18px; font-weight: bold; color: #e74c3c; }
        .nav { display: flex; gap: 8px; margin-bottom: 20px; }
        .nav a { color: #3498db; text-decoration: none; padding: 8px 16px; background: #253545; border-radius: 6px; }
        .nav a:hover { background: #2a3a4a; }
    </style>
</head>
<body>
<div class="container">
    <div class="nav">
        <a href="/">← 定投主页</a>
        <a href="/stop_profit">🔄 止盈轮动</a>
    </div>

    <div class="header">
        <h1>🔄 止盈轮动追踪</h1>
        <p>止盈阈值 """ + str(int(STOP_PROFIT_CONFIG_WEB['threshold'] * 100)) + """% | 再投策略：低配类别优先 | 自动刷新 30s</p>
    </div>

    <div class="refresh-time" id="refresh-time"></div>

    <div id="signals-area"></div>

    <div class="actions">
        <button class="btn btn-danger" onclick="executeStopProfit()">⚡ 执行止盈轮动检查</button>
        <button class="btn btn-primary" onclick="loadData(true)">🔄 刷新数据</button>
    </div>

    <div class="grid">
        <div class="card">
            <h2>📊 ETF 盈亏追踪</h2>
            <div id="etf-list">加载中...</div>
        </div>
        <div class="card">
            <h2>📋 类别配比偏差</h2>
            <div class="category-grid" id="category-grid">加载中...</div>
        </div>
    </div>

    <div class="card" style="margin-bottom:20px">
        <h2>📜 最近止盈记录</h2>
        <div id="history-area">加载中...</div>
    </div>
</div>

<script>
const THRESHOLD = """ + str(int(STOP_PROFIT_CONFIG_WEB['threshold'] * 100)) + """;

function loadData(isInitial) {
    // 首次加载时显示加载中，自动刷新时保留旧数据
    if (isInitial) {
        document.getElementById('etf-list').innerHTML = '<p style="color:#7f8c8d">加载中...</p>';
        document.getElementById('category-grid').innerHTML = '<p style="color:#7f8c8d">加载中...</p>';
        document.getElementById('signals-area').innerHTML = '<p style="color:#7f8c8d">加载中...</p>';
        document.getElementById('history-area').innerHTML = '<p style="color:#7f8c8d">加载中...</p>';
    }
    
    fetch('/api/stop_profit/status')
        .then(r => {
            if (!r.ok) {
                throw new Error('网络请求失败: ' + r.status);
            }
            return r.json();
        })
        .then(data => {
            if (data.error) {
                document.getElementById('etf-list').innerHTML = '<p style="color:#e74c3c">加载失败: ' + data.error + '</p>';
                console.error('API错误:', data.error);
                return;
            }
            renderETFList(data.holdings_info || []);
            renderCategoryGrid(data.category_allocation || {});
            renderSignals(data.signals || []);
            renderHistory(data.history || []);
            document.getElementById('refresh-time').textContent = '最后刷新: ' + new Date().toLocaleTimeString();
        })
        .catch(error => {
            document.getElementById('etf-list').innerHTML = '<p style="color:#e74c3c">加载失败: ' + error.message + '</p>';
            document.getElementById('category-grid').innerHTML = '<p style="color:#7f8c8d">加载失败</p>';
            document.getElementById('signals-area').innerHTML = '<p style="color:#7f8c8d">加载失败</p>';
            document.getElementById('history-area').innerHTML = '<p style="color:#7f8c8d">加载失败</p>';
            console.error('加载数据失败:', error);
        });
}

function renderETFList(holdings) {
    const el = document.getElementById('etf-list');
    if (!holdings.length) { el.innerHTML = '<p style="color:#7f8c8d">暂无持仓数据</p>'; return; }
    el.innerHTML = holdings.map(h => {
        const pct = h.profit_pct;
        const color = pct >= 0 ? 'positive' : 'negative';
        const barPct = Math.min(Math.abs(pct) / THRESHOLD * 100, 100);
        const barClass = pct >= 0 ? 'progress-positive' : 'progress-negative';
        const triggerAt = THRESHOLD;
        const triggerPos = THRESHOLD / (Math.max(Math.abs(pct), THRESHOLD) * 1.5) * 100;
        const needGain = h.need_gain ? h.need_gain.toFixed(4) : '-';
        return `<div class="etf-row">
            <div>
                <div class="etf-name">${h.code} ${h.name}</div>
                <div style="font-size:12px;color:#7f8c8d">持仓${h.shares}股 | 成本¥${h.avg_cost.toFixed(4)} | 现价¥${h.current_price.toFixed(4)}</div>
            </div>
            <div style="text-align:right">
                <div class="etf-profit ${color}">${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%</div>
                <div style="font-size:11px;color:#7f8c8d">距止盈需+${h.distance.toFixed(1)}% | 目标价¥${needGain}</div>
                <div class="progress-bar trigger-line">
                    <div class="progress-fill ${barClass}" style="width:${barPct}%"></div>
                    <div class="trigger-mark" style="left:${(THRESHOLD / (THRESHOLD + Math.abs(pct)) * 100).toFixed(0)}%"></div>
                </div>
            </div>
        </div>`;
    }).join('');
}

function renderCategoryGrid(catAlloc) {
    const el = document.getElementById('category-grid');
    const cats = Object.entries(catAlloc);
    if (!cats.length) { el.innerHTML = '<p style="color:#7f8c8d;grid-column:1/-1">暂无配比数据</p>'; return; }
    el.innerHTML = cats.map(([name, info]) => {
        let cls = info.deviation < -1 ? 'under' : (info.deviation > 1 ? 'over' : 'balanced');
        return `<div class="cat-item">
            <div class="cat-name">${name}</div>
            <div class="cat-pct">${info.current_pct}%</div>
            <div style="font-size:11px;color:#7f8c8d">目标 ${info.target_pct}%</div>
            <div class="cat-deviation ${cls}">${info.deviation > 0 ? '+' : ''}${info.deviation}%</div>
        </div>`;
    }).join('');
}

function renderSignals(signals) {
    const el = document.getElementById('signals-area');
    if (!signals || !signals.length) {
        el.innerHTML = '';
        return;
    }
    el.innerHTML = signals.map(s => `<div class="signal-alert">
        ⚡ <span class="code">${s.code} (${s.name})</span> 触发止盈！
        盈利 <span style="color:#e74c3c;font-weight:bold">${s.profit_pct}%</span> ≥ ${s.threshold}%
        市值 ¥${s.market_value.toFixed(2)} | 盈亏 ¥${s.profit_amount.toFixed(2)}
    </div>`).join('');
}

function renderHistory(history) {
    const el = document.getElementById('history-area');
    if (!history || !history.length) { el.innerHTML = '<p style="color:#7f8c8d">暂无止盈记录</p>'; return; }
    el.innerHTML = '<table style="width:100%;border-collapse:collapse;color:#e0e0e0"><tr style="border-bottom:1px solid #2a3a4a"><th style="padding:8px;text-align:left">日期</th><th>止盈</th><th>释放资金</th><th>再投</th></tr>' +
        history.slice().reverse().map(h => `<tr style="border-bottom:1px solid #253545">
            <td style="padding:8px">${h.date} ${h.time || ''}</td>
            <td style="color:#e74c3c">${h.stop_profit_count || (h.stop_profit_trades ? h.stop_profit_trades.length : 0)}笔</td>
            <td style="color:#e74c3c">¥${h.total_freed.toFixed(2)}</td>
            <td style="color:#2ecc71">${h.reinvest_count || (h.reinvest_trades ? h.reinvest_trades.length : 0)}笔 ¥${h.total_reinvested.toFixed(2)}</td>
        </tr>`).join('') + '</table>';
}

function executeStopProfit() {
    if (!confirm('确定要执行止盈轮动检查吗？\\n\\n系统将检查所有持仓，如有达到""" + str(int(STOP_PROFIT_CONFIG_WEB['threshold'] * 100)) + """%盈利的ETF将自动止盈并再投资。')) return;
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = '执行中...';
    fetch('/api/stop_profit/execute', {method: 'POST'})
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                alert('止盈轮动完成！\\n止盈: ' + data.stop_profit_count + '笔\\n再投: ' + data.reinvest_count + '笔\\n释放资金: ¥' + data.total_freed.toFixed(2));
            } else {
                alert('执行失败: ' + (data.message || '未知错误'));
            }
            loadData();
        })
        .finally(() => { btn.disabled = false; btn.textContent = '⚡ 执行止盈轮动检查'; });
}

document.addEventListener('DOMContentLoaded', () => loadData(true));
setInterval(() => loadData(false), 30000);
</script>
</body>
</html>
"""


if __name__ == '__main__':
    run()
