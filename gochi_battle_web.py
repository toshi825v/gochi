#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, jsonify, session
import random
import os
import json
import uuid

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ゲームデータ
class GameState:
    def __init__(self):
        self.player_name = ""
        self.cpu_names = ["田中", "佐藤", "鈴木", "高橋"]
        self.players = []  # プレイヤー名のリスト（自分+CPU）
        self.menu = {}  # メニュー名: 価格
        self.menu_display = {}  # メニュー名: 表示名（価格非表示）
        self.orders = {}  # プレイヤー名: [注文リスト]
        self.target_price = 20000
        self.current_player_index = 0  # 現在の注文プレイヤーのインデックス
        self.players_finished = set()  # 注文を終了したプレイヤーの集合
        self.turn_count = 0  # 現在のターン数
        self.difficulty = "普通"
        self.game_log = []
        self.setup_menu()
        
    def setup_menu(self):
        """基本的なメニューをセットアップする"""
        menu_items = {
            # メインディッシュ
            "特選和牛ステーキ": {"price": 12000, "description": "最高級の和牛を使用した贅沢なステーキ"},
            "フォアグラのソテー": {"price": 8000, "description": "なめらかな食感が特徴の高級食材"},
            "トリュフリゾット": {"price": 6000, "description": "香り高いトリュフを使用した本格リゾット"},
            "キャビアカナッペ": {"price": 5000, "description": "黒いダイヤと呼ばれる高級食材を使用"},
            "ロブスターのグリル": {"price": 9000, "description": "新鮮なロブスターを丁寧に焼き上げた一品"},
            "シーフードパスタ": {"price": 3500, "description": "海の幸をふんだんに使用したパスタ"},
            "フレンチコース": {"price": 15000, "description": "シェフ特製の豪華フルコース"},
            "高級寿司盛り合わせ": {"price": 10000, "description": "厳選された旬の魚を使用した特上寿司"},
            "和牛しゃぶしゃぶ": {"price": 7500, "description": "とろけるような食感の和牛を楽しめる"},
            "季節の天ぷら": {"price": 4000, "description": "旬の食材を使用した揚げたて天ぷら"},
            "サラダ": {"price": 1200, "description": "新鮮な野菜を使用したシンプルなサラダ"},
            "デザート盛り合わせ": {"price": 2000, "description": "パティシエ特製の甘味の数々"},
            
            # 追加料理
            "黒毛和牛サーロイン": {"price": 13500, "description": "最高級の黒毛和牛を使用した極上のサーロインステーキ"},
            "トリュフオムレツ": {"price": 7000, "description": "高級トリュフをふんだんに使用した特製オムレツ"},
            "金目鯛の煮付け": {"price": 6500, "description": "脂がのった金目鯛を丁寧に煮込んだ逸品"},
            "伊勢海老の鬼殻焼き": {"price": 11000, "description": "新鮮な伊勢海老を豪快に焼き上げた一品"},
            "松茸の土瓶蒸し": {"price": 8500, "description": "秋の味覚の王様を贅沢に使用した風味豊かな一品"},
            "ふぐ刺し": {"price": 9500, "description": "熟練の職人が調理した極薄のふぐ刺し"},
            "神戸牛ステーキ": {"price": 14000, "description": "世界に誇る神戸牛を使用した極上ステーキ"},
            "あわびの肝ソース": {"price": 10500, "description": "新鮮なあわびを肝ソースで味わう贅沢料理"},
            "うに丼": {"price": 8800, "description": "濃厚な味わいの最高級うにをたっぷりと"},
            "ズワイガニのグラタン": {"price": 7200, "description": "ズワイガニの身をふんだんに使用した濃厚グラタン"},
            "フカヒレの姿煮": {"price": 12500, "description": "高級食材フカヒレを丸ごと使用した豪華な一品"},
            "和牛すき焼き": {"price": 9800, "description": "最高級の和牛を使用した伝統的なすき焼き"}
        }
        
        for name, info in menu_items.items():
            self.menu[name] = info["price"]
            self.menu_display[name] = info["description"]
    
    def start_game(self, player_name, target_price, difficulty):
        self.player_name = player_name
        self.players = [self.player_name] + self.cpu_names
        self.orders = {player: [] for player in self.players}
        self.players_finished = set()
        self.target_price = target_price
        self.difficulty = difficulty
        self.current_player_index = 0
        self.turn_count = 1
        self.game_log = []
        
        # 開始メッセージ
        self.game_log.append(f"ゲームを開始します！")
        self.game_log.append(f"目標金額: {self.target_price:,}円")
        self.game_log.append(f"プレイヤー: {self.player_name}さん")
        self.game_log.append(f"CPUプレイヤー: {', '.join(self.cpu_names)}さん")
        self.game_log.append(f"順番に1品ずつ料理を注文します。自分の番が来たら「料理を注文」か「STOP」を選択してください。")
        
        return {
            "current_player": self.players[self.current_player_index],
            "turn_count": self.turn_count,
            "is_player_turn": self.players[self.current_player_index] == self.player_name,
            "game_log": self.game_log
        }
    
    def order_item(self, menu_name):
        current_player = self.players[self.current_player_index]
        self.orders[current_player].append(menu_name)
        self.game_log.append(f"{current_player}さんが「{menu_name}」を注文しました。")
        
        return self.next_player()
    
    def stop_ordering(self):
        current_player = self.players[self.current_player_index]
        self.players_finished.add(current_player)
        self.game_log.append(f"{current_player}さんが注文を終了しました。")
        
        return self.next_player()
    
    def cpu_order_turn(self):
        current_player = self.players[self.current_player_index]
        orders_count = len(self.orders[current_player])
        stop_probability = 0
        
        if self.difficulty == "簡単":
            # 簡単: 早めにSTOP
            if orders_count == 0:
                stop_probability = 0.1  # 最初から10%の確率でSTOP
            elif orders_count == 1:
                stop_probability = 0.3  # 1品注文後は30%の確率でSTOP
            elif orders_count == 2:
                stop_probability = 0.6  # 2品注文後は60%の確率でSTOP
            else:
                stop_probability = 0.9  # 3品以上注文後は90%の確率でSTOP
        elif self.difficulty == "普通":
            # 普通: 適度にSTOP
            if orders_count == 0:
                stop_probability = 0.05  # 最初から5%の確率でSTOP
            elif orders_count == 1:
                stop_probability = 0.2  # 1品注文後は20%の確率でSTOP
            elif orders_count == 2:
                stop_probability = 0.4  # 2品注文後は40%の確率でSTOP
            elif orders_count == 3:
                stop_probability = 0.7  # 3品注文後は70%の確率でSTOP
            else:
                stop_probability = 0.85  # 4品以上注文後は85%の確率でSTOP
        else:  # 難しい
            # 難しい: 遅めにSTOP
            if orders_count == 0:
                stop_probability = 0  # 最初はSTOPしない
            elif orders_count == 1:
                stop_probability = 0.1  # 1品注文後は10%の確率でSTOP
            elif orders_count == 2:
                stop_probability = 0.2  # 2品注文後は20%の確率でSTOP
            elif orders_count == 3:
                stop_probability = 0.4  # 3品注文後は40%の確率でSTOP
            else:
                stop_probability = 0.6  # 4品以上注文後は60%の確率でSTOP
        
        # STOPするかどうか決定
        if random.random() < stop_probability:
            # STOP
            self.players_finished.add(current_player)
            self.game_log.append(f"{current_player}さんが注文を終了しました。")
        else:
            # 注文する
            menu_items = list(self.menu.keys())
            
            # 難易度に応じて料理の選び方を変える
            if self.difficulty == "簡単":
                # 安い料理を選びがち
                sorted_items = sorted(menu_items, key=lambda x: self.menu[x])
                item = random.choice(sorted_items[:10])
            elif self.difficulty == "普通":
                # ランダム
                item = random.choice(menu_items)
            else:  # 難しい
                # 高い料理を選びがち
                sorted_items = sorted(menu_items, key=lambda x: self.menu[x], reverse=True)
                item = random.choice(sorted_items[:10])
                
            # 注文を記録
            self.orders[current_player].append(item)
            self.game_log.append(f"{current_player}さんが「{item}」を注文しました。")
        
        return self.next_player()
    
    def next_player(self):
        # 次のプレイヤーを探す
        for _ in range(len(self.players)):
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            
            # 一周したらターン数を増やす
            if self.current_player_index == 0:
                self.turn_count += 1
                
            current_player = self.players[self.current_player_index]
            
            # まだ注文を終えていないプレイヤーなら選択
            if current_player not in self.players_finished:
                break
        else:
            # 全員が注文を終えた場合は結果表示
            return self.get_results()
        
        # 現在のプレイヤーがCPUなら自動で注文
        if self.players[self.current_player_index] != self.player_name:
            return {
                "current_player": self.players[self.current_player_index],
                "turn_count": self.turn_count,
                "is_player_turn": False,
                "is_cpu_turn": True,
                "game_log": self.game_log
            }
        else:
            return {
                "current_player": self.players[self.current_player_index],
                "turn_count": self.turn_count,
                "is_player_turn": True,
                "game_log": self.game_log
            }
    
    def calculate_total(self, player):
        """プレイヤーの合計金額を計算する"""
        total = 0
        for item in self.orders[player]:
            total += self.menu[item]
        return total
    
    def get_results(self):
        results = {
            "game_over": True,
            "target_price": self.target_price,
            "players_results": [],
            "game_log": self.game_log
        }
        
        totals = {}
        diffs = {}  # 目標金額との差額
        
        for player in self.players:
            total = self.calculate_total(player)
            totals[player] = total
            diffs[player] = abs(total - self.target_price)
            
            player_result = {
                "name": player,
                "orders": [],
                "total": total,
                "diff": diffs[player]
            }
            
            for item in self.orders[player]:
                player_result["orders"].append({
                    "name": item,
                    "price": self.menu[item]
                })
            
            results["players_results"].append(player_result)
        
        # 目標金額に最も遠い人を見つける（敗者）
        max_diff = max(diffs.values()) if diffs else 0
        losers = [player for player, diff in diffs.items() if diff == max_diff]
        
        # 目標金額に最も近い人を見つける（勝者）
        min_diff = min(diffs.values()) if diffs else float('inf')
        winners = [player for player, diff in diffs.items() if diff == min_diff]
        
        results["winners"] = winners
        results["losers"] = losers
        results["is_player_winner"] = self.player_name in winners
        results["is_player_loser"] = self.player_name in losers
        
        return results

# ゲームインスタンスを保存する辞書
games = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/new_game', methods=['POST'])
def new_game():
    data = request.json
    player_name = data.get('player_name', '')
    target_price = int(data.get('target_price', 20000))
    difficulty = data.get('difficulty', '普通')
    
    if not player_name:
        return jsonify({"error": "プレイヤー名を入力してください"}), 400
    
    # 新しいゲームIDを生成
    game_id = str(uuid.uuid4())
    
    # 新しいゲームインスタンスを作成
    game = GameState()
    game_state = game.start_game(player_name, target_price, difficulty)
    
    # ゲームを保存
    games[game_id] = game
    
    # セッションにゲームIDを保存
    session['game_id'] = game_id
    
    return jsonify({
        "game_id": game_id,
        "state": game_state,
        "menu": [{"name": name, "description": desc} for name, desc in game.menu_display.items()]
    })

@app.route('/api/order_item', methods=['POST'])
def order_item():
    data = request.json
    game_id = session.get('game_id')
    menu_name = data.get('menu_name')
    
    if not game_id or game_id not in games:
        return jsonify({"error": "ゲームが見つかりません"}), 404
    
    game = games[game_id]
    result = game.order_item(menu_name)
    
    return jsonify(result)

@app.route('/api/stop_ordering', methods=['POST'])
def stop_ordering():
    game_id = session.get('game_id')
    
    if not game_id or game_id not in games:
        return jsonify({"error": "ゲームが見つかりません"}), 404
    
    game = games[game_id]
    result = game.stop_ordering()
    
    return jsonify(result)

@app.route('/api/cpu_turn', methods=['POST'])
def cpu_turn():
    game_id = session.get('game_id')
    
    if not game_id or game_id not in games:
        return jsonify({"error": "ゲームが見つかりません"}), 404
    
    game = games[game_id]
    result = game.cpu_order_turn()
    
    return jsonify(result)

if __name__ == '__main__':
    # テンプレートフォルダが存在しない場合は作成
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # 静的ファイルフォルダが存在しない場合は作成
    if not os.path.exists('static'):
        os.makedirs('static')
    
    app.run(debug=True, host='0.0.0.0', port=5000)
