# 导入 Flask 框架相关模块，用于创建 Web 应用
from flask import Flask, render_template, request, jsonify
# 导入 os 模块，用于操作系统相关功能，如文件路径操作等
import os
# 导入 pandas 库，用于数据处理和分析
import pandas as pd
# 从 weather_scraper.py 文件中导入 AdvancedWeatherSpider 类和 save_to_csv 函数
from weather_scraper import AdvancedWeatherSpider, save_to_csv

# 创建 Flask 应用实例，指定模板文件夹为 'templates'
app = Flask(__name__, template_folder='templates')

# 实例化 AdvancedWeatherSpider 类，用于抓取天气数据
spider = AdvancedWeatherSpider()

# 定义根路由，当用户访问网站根目录时，执行此函数
@app.route('/')
def index():
    # 渲染 index.html 模板文件并返回给客户端
    return render_template('index.html')

# 定义 /get_weather 路由，仅允许 POST 请求
@app.route('/get_weather', methods=['POST'])
def get_weather():
    # 从 POST 请求的表单数据中获取城市名称，如果未提供则默认使用 '北京'
    city = request.form.get('city', '北京')
    try:
        # 调用 spider 的 crawl_weather 方法，获取指定城市的天气数据
        data = spider.crawl_weather(city)
        # 将获取到的天气数据转换为 pandas 的 DataFrame 对象
        df = pd.DataFrame(data)
        # 检查 DataFrame 是否为空，如果为空则返回错误信息给客户端
        if df.empty:
            return jsonify({'status': 'error', 'message': f'未能获取{city}的天气数据'})
        # 调用 save_to_csv 函数，将天气数据保存为 CSV 文件，并获取文件路径
        csv_path = save_to_csv(df, city)
        # 从 DataFrame 中提取日期列，并转换为列表
        dates = df['日期'].tolist()
        # 从 DataFrame 中提取温度列并转换为列表，如果列不存在则使用长度为 dates 列表长度的 None 列表
        temps = df['温度'].tolist() if '温度' in df.columns else [None]*len(dates)
        # 从 DataFrame 中提取最高温度列并转换为列表，如果列不存在则使用长度为 dates 列表长度的 None 列表
        high_temps = df['最高温度'].tolist() if '最高温度' in df.columns else [None]*len(dates)
        # 从 DataFrame 中提取最低温度列并转换为列表，如果列不存在则使用长度为 dates 列表长度的 None 列表
        low_temps = df['最低温度'].tolist() if '最低温度' in df.columns else [None]*len(dates)
        # 从 DataFrame 中提取湿度列并转换为列表，如果列不存在则使用长度为 dates 列表长度的 None 列表
        humidity = df['湿度'].tolist() if '湿度' in df.columns else [None]*len(dates)
        # 从 DataFrame 中提取紫外线列并转换为列表，如果列不存在则使用长度为 dates 列表长度的 None 列表
        uv = df['紫外线'].tolist() if '紫外线' in df.columns else [None]*len(dates)
        # 从 DataFrame 中提取空气质量列并转换为列表，如果列不存在则使用长度为 dates 列表长度的 None 列表
        aqi = df['空气质量'].tolist() if '空气质量' in df.columns else [None]*len(dates)
        # 从 DataFrame 中提取风向列并转换为列表，如果列不存在则使用长度为 dates 列表长度的 None 列表
        wind_direction = df['风向'].tolist() if '风向' in df.columns else [None]*len(dates)
        # 从 DataFrame 中提取风级列并转换为列表，如果列不存在则使用长度为 dates 列表长度的 None 列表
        wind_level = df['风级'].tolist() if '风级' in df.columns else [None]*len(dates)
        # 从 DataFrame 中提取体感温度列并转换为列表，如果列不存在则使用长度为 dates 列表长度的 None 列表
        feel_temp = df['体感温度'].tolist() if '体感温度' in df.columns else [None]*len(dates)
        # 从 DataFrame 中提取天气列并转换为列表，如果列不存在则使用长度为 dates 列表长度的 None 列表
        weather = df['天气'].tolist() if '天气' in df.columns else [None]*len(dates)
        # 从 DataFrame 中提取能见度列并转换为列表，如果列不存在则使用长度为 dates 列表长度的 None 列表
        visibility = df['能见度'].tolist() if '能见度' in df.columns else [None]*len(dates)
        # 从 DataFrame 中提取降雨量列并转换为列表，如果列不存在则使用长度为 dates 列表长度的 None 列表
        rainfall = df['降雨量'].tolist() if '降雨量' in df.columns else [None]*len(dates)

        # 将处理后的数据以 JSON 格式返回给客户端，包含状态信息、原始数据和用于图表展示的数据
        return jsonify({
            'status': 'success',
            'data': df.to_dict('records'),
            'chart_data': {
                'dates': dates,
                'temps': temps,
                'high_temps': high_temps,
                'low_temps': low_temps,
                'humidity': humidity,
                'uv': uv,
                'aqi': aqi,
                'wind_direction': wind_direction,
                'wind_level': wind_level,
                'feel_temp': feel_temp,
                'weather': weather,
                'visibility': visibility,
                'rainfall': rainfall
            }
        })
    except Exception as e:
        # 如果发生异常，将异常信息以 JSON 格式返回给客户端，状态为错误
        return jsonify({'status': 'error', 'message': str(e)})

# 当脚本作为主程序运行时，启动 Flask 应用
if __name__ == '__main__':
    # 以调试模式运行应用，监听 5000 端口
    app.run(debug=True, port=5000)