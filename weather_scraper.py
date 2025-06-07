import requests
from bs4 import BeautifulSoup
import pandas as pd
import random
import json
import os


# API_KEY = "7f23dd35da76e75c64030c21f548d19d"  # 连接不上聚合数据的端口，所以爬了中国天气网的数据

class AdvancedWeatherSpider:
    """高级天气爬虫类，负责获取和处理天气数据"""

    def __init__(self):
        # 设置HTTP请求头，模拟浏览器行为，避免被网站反爬机制拦截
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            'Referer': 'http://www.weather.com.cn/'
        }
        # 中国天气网的基础URL
        self.base_url = "http://www.weather.com.cn/weather/"
        # 各地区城市代码列表的URL
        self.city_code_urls = [
            "http://www.weather.com.cn/textFC/hb.shtml",  # 华北地区
            "http://www.weather.com.cn/textFC/db.shtml",  # 东北地区
            "http://www.weather.com.cn/textFC/hd.shtml",  # 华东地区
            "http://www.weather.com.cn/textFC/hz.shtml",  # 华中地区
            "http://www.weather.com.cn/textFC/hn.shtml",  # 华南地区
            "http://www.weather.com.cn/textFC/xb.shtml",  # 西北地区
            "http://www.weather.com.cn/textFC/xn.shtml",  # 西南地区
            "http://www.weather.com.cn/textFC/gat.shtml"  # 港澳台地区
        ]
        # 加载所有城市代码映射表
        self.all_city_codes = self.load_all_city_codes()

    def load_all_city_codes(self):
        """加载所有城市代码，返回城市名称到代码的映射字典"""
        city_codes = {}
        # 遍历各地区URL，抓取城市代码
        for url in self.city_code_urls:
            try:
                resp = requests.get(url, headers=self.headers, timeout=15)
                resp.encoding = 'utf-8'
                soup = BeautifulSoup(resp.text, 'lxml')
                tables = soup.select("div.conMidtab table")
                # 解析每个表格中的城市信息
                for table in tables:
                    trs = table.find_all("tr")[2:]  # 跳过表头
                    for tr in trs:
                        tds = tr.find_all("td")
                        if len(tds) >= 8:
                            city_name = tds[1].get_text(strip=True)
                            a_tag = tds[1].find("a")
                            if not a_tag or not a_tag.get("href"):
                                continue
                            # 从URL中提取城市代码
                            city_url = a_tag["href"]
                            city_code = city_url.split("/")[-1].replace(".shtml", "")
                            city_codes[city_name] = city_code
            except Exception as e:
                print(f"抓取{url}时出错：{e}")
        print(f"共获取到{len(city_codes)}个城市代码")
        # 如果未获取到任何城市代码，使用默认值
        return city_codes if city_codes else {'北京市': '101010100'}

    def get_city_code(self, city_name):
        """根据城市名称获取对应的城市代码，支持多种匹配方式"""
        # 精确匹配
        if city_name in self.all_city_codes:
            return self.all_city_codes[city_name]
        # 模糊匹配
        for name in self.all_city_codes:
            if city_name in name:
                return self.all_city_codes[name]
        # 处理以"市"结尾的城市名
        for name in self.all_city_codes:
            if city_name.endswith('市') and name.endswith(city_name):
                return self.all_city_codes[name]
        # 分词匹配
        parts = city_name.split('市')
        if len(parts) > 1:
            for name in self.all_city_codes:
                if all(part in name for part in parts if part):
                    return self.all_city_codes[name]
        # 默认返回北京代码
        print(f"未找到城市: {city_name}，使用默认北京")
        return self.all_city_codes.get('北京市', '101010100')

    def fetch_weather_data(self, city_name="北京"):
        """获取指定城市的天气数据"""
        city_code = self.get_city_code(city_name)
        url = f"{self.base_url}{city_code}.shtml"
        resp = requests.get(url, headers=self.headers, timeout=10)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, "lxml")
        data = []

        # 解析网页中的天气信息
        for idx, li in enumerate(soup.select("ul.t.clearfix li")):
            date = li.find("h1").text if li.find("h1") else ""
            weather = li.find("p", class_="wea").text if li.find("p", class_="wea") else ""
            temp = li.find("p", class_="tem").text.replace("\n", "").replace(" ", "") if li.find("p",
                                                                                                 class_="tem") else ""
            wind = li.find("p", class_="win").find("i").text if li.find("p", class_="win") and li.find("p",
                                                                                                       class_="win").find(
                "i") else ""
            wind_dir = li.find("p", class_="win").find("span")['title'] if li.find("p", class_="win") and li.find("p",
                                                                                                                  class_="win").find(
                "span") else ""

            # 解析温度数据
            try:
                if '℃' in temp:
                    temps = [int(t.replace('℃', '')) for t in temp.split('/') if t.strip()]
                    if len(temps) == 2:
                        high_temp, low_temp = temps
                        avg_temp = (high_temp + low_temp) // 2
                    elif len(temps) == 1:
                        high_temp = low_temp = avg_temp = temps[0]
                    else:
                        high_temp = low_temp = avg_temp = None
                else:
                    high_temp = low_temp = avg_temp = None
            except Exception:
                high_temp = low_temp = avg_temp = None
            #中国天气网中不提供以下数据，所以为模拟数据
            # 推测/随机生成的字段（实际项目中可替换为真实API数据）
            humidity = random.randint(30, 90)  # 随机生成湿度值
            uv = random.randint(1, 11)  # 随机生成紫外线指数
            aqi = random.choice(['优', '良', '轻度污染', '中度污染', '重度污染', '严重污染'])  # 随机生成空气质量
            feel_temp = avg_temp + random.randint(-2, 2) if avg_temp is not None else "-"  # 计算体感温度
            visibility = random.randint(5, 20)  # 随机生成能见度
            rainfall = random.randint(0, 10)  # 随机生成降雨量
            weather_type = "实时" if idx == 0 else "预报"  # 区分实时和预报数据

            data.append({
                "日期": date,
                "类型": weather_type,
                "温度": avg_temp if avg_temp is not None else "-",
                "最高温度": high_temp if high_temp is not None else "-",
                "最低温度": low_temp if low_temp is not None else "-",
                "湿度": humidity,
                "紫外线": uv,
                "空气质量": aqi,
                "风向": wind_dir,
                "风级": wind,
                "体感温度": feel_temp,
                "天气": weather,
                "能见度": visibility,
                "降雨量": rainfall
            })
        return data

    def crawl_weather(self, city_name):
        """爬取指定城市的天气数据（对外接口）"""
        return self.fetch_weather_data(city_name)


def save_to_csv(data, filepath):
    """将天气数据保存为CSV文件"""
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False, encoding='utf-8-sig')


def scrape_city_codes():
    """独立的城市代码爬取函数（可单独运行）"""
    base_url = "http://www.weather.com.cn/textFC/"
    provinces = [
        "hb", "db", "hd", "hz", "hn", "xb", "xn", "gat"
    ]
    all_city_codes = {}

    for prov in provinces:
        prov_url = f"{base_url}{prov}.shtml"
        print(f"抓取{prov_url}")
        try:
            resp = requests.get(prov_url, timeout=10)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "lxml")
            tables = soup.select("div.conMidtab table")
            for table in tables:
                trs = table.find_all("tr")[2:]  # 跳过表头
                for tr in trs:
                    tds = tr.find_all("td")
                    if len(tds) >= 8:
                        city_name = tds[1].get_text(strip=True)
                        a_tag = tds[1].find("a")
                        if not a_tag or not a_tag.get("href"):
                            continue
                        city_url = a_tag["href"]
                        city_code = city_url.split("/")[-1].replace(".shtml", "")
                        all_city_codes[city_name] = city_code
        except Exception as e:
            print(f"抓取{prov_url}时出错：{e}")

    # 保存城市代码为JSON文件
    with open("city_codes.json", "w", encoding="utf-8") as f:
        json.dump(all_city_codes, f, ensure_ascii=False, indent=2)
    print(f"共获取到{len(all_city_codes)}个城市代码，已保存到city_codes.json")


# 单例模式创建爬虫实例
_spider = AdvancedWeatherSpider()


def fetch_weather_data(city_name="北京"):
    """便捷函数：获取天气数据（使用单例爬虫）"""
    return _spider.fetch_weather_data(city_name)


if __name__ == "__main__":
    # 测试代码：直接运行时获取北京天气数据
    spider = AdvancedWeatherSpider()
    data = spider.fetch_weather_data("北京")
    print(data)
