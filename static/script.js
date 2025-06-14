document.addEventListener('DOMContentLoaded', function() {
    // タブ切り替え
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabPanels = document.querySelectorAll('.tab-panel');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            // タブボタンのアクティブ状態を切り替え
            tabButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // タブパネルの表示を切り替え
            const targetId = this.id.replace('-btn', '');
            tabPanels.forEach(panel => {
                panel.classList.remove('active');
                if (panel.id === targetId) {
                    panel.classList.add('active');
                }
            });
        });
    });
    
    // 目標金額設定ボタン
    const setTargetBtn = document.getElementById('set-target-btn');
    setTargetBtn.addEventListener('click', function() {
        const targetPrice = document.getElementById('target-price').value;
        if (targetPrice <= 0) {
            alert('目標金額は正の整数を入力してください。');
            return;
        }
        alert(`目標金額を${Number(targetPrice).toLocaleString()}円に設定しました。`);
    });
    
    // ゲーム開始ボタン
    const startGameBtn = document.getElementById('start-game-btn');
    startGameBtn.addEventListener('click', startGame);
    
    // 注文ボタン
    const orderBtn = document.getElementById('order-btn');
    orderBtn.addEventListener('click', orderItem);
    
    // STOP（注文終了）ボタン
    const stopBtn = document.getElementById('stop-btn');
    stopBtn.addEventListener('click', stopOrdering);
    
    // 新しいゲームボタン
    const newGameBtn = document.getElementById('new-game-btn');
    newGameBtn.addEventListener('click', function() {
        document.getElementById('setup-tab-btn').click();
    });
    
    // メニューテーブルの行選択
    const menuTable = document.getElementById('menu-table');
    menuTable.addEventListener('click', function(e) {
        const target = e.target.closest('tr');
        if (!target || target.parentElement.tagName === 'THEAD') return;
        
        // 選択状態を切り替え
        const rows = menuTable.querySelectorAll('tbody tr');
        rows.forEach(row => row.classList.remove('selected'));
        target.classList.add('selected');
    });
    
    // ゲーム状態
    let gameState = {
        gameId: null,
        currentPlayer: '',
        turnCount: 0,
        isPlayerTurn: false,
        menu: [],
        gameLog: []
    };
    
    // ゲーム開始
    function startGame() {
        const playerName = document.getElementById('player-name').value.trim();
        if (!playerName) {
            alert('あなたの名前を入力してください。');
            return;
        }
        
        const targetPrice = parseInt(document.getElementById('target-price').value);
        const difficulty = document.querySelector('input[name="difficulty"]:checked').value;
        
        fetch('/api/new_game', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                player_name: playerName,
                target_price: targetPrice,
                difficulty: difficulty
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            
            gameState = {
                gameId: data.game_id,
                currentPlayer: data.state.current_player,
                turnCount: data.state.turn_count,
                isPlayerTurn: data.state.is_player_turn,
                menu: data.menu,
                gameLog: data.state.game_log
            };
            
            // メニューを表示
            updateMenuTable();
            
            // ゲームログを表示
            updateGameLog();
            
            // 現在のプレイヤー情報を更新
            updateCurrentPlayerInfo();
            
            // プレイタブに切り替え
            document.getElementById('play-tab-btn').click();
            
            // CPUのターンなら自動で処理
            if (!gameState.isPlayerTurn) {
                processCpuTurn();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('ゲーム開始中にエラーが発生しました。');
        });
    }
    
    // メニューテーブルを更新
    function updateMenuTable() {
        const menuItems = document.getElementById('menu-items');
        menuItems.innerHTML = '';
        
        gameState.menu.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.name}</td>
                <td>${item.description}</td>
            `;
            row.dataset.menuName = item.name;
            menuItems.appendChild(row);
        });
    }
    
    // ゲームログを更新
    function updateGameLog() {
        const orderHistory = document.getElementById('order-history');
        orderHistory.innerHTML = gameState.gameLog.join('<br>');
        orderHistory.scrollTop = orderHistory.scrollHeight;
    }
    
    // 現在のプレイヤー情報を更新
    function updateCurrentPlayerInfo() {
        const currentPlayerElement = document.getElementById('current-player');
        const turnCountElement = document.getElementById('turn-count');
        
        currentPlayerElement.textContent = `現在の注文者: ${gameState.currentPlayer}さん`;
        turnCountElement.textContent = `ターン: ${gameState.turnCount}`;
        
        // プレイヤーのターンかどうかでボタンの有効/無効を切り替え
        const orderBtn = document.getElementById('order-btn');
        const stopBtn = document.getElementById('stop-btn');
        
        if (gameState.isPlayerTurn) {
            orderBtn.disabled = false;
            stopBtn.disabled = false;
        } else {
            orderBtn.disabled = true;
            stopBtn.disabled = true;
        }
    }
    
    // 料理を注文
    function orderItem() {
        const selectedRow = document.querySelector('#menu-table tbody tr.selected');
        if (!selectedRow) {
            alert('注文する料理を選択してください。');
            return;
        }
        
        const menuName = selectedRow.dataset.menuName;
        
        fetch('/api/order_item', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                menu_name: menuName
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            
            handleGameStateUpdate(data);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('注文中にエラーが発生しました。');
        });
    }
    
    // 注文を終了
    function stopOrdering() {
        fetch('/api/stop_ordering', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            
            handleGameStateUpdate(data);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('注文終了中にエラーが発生しました。');
        });
    }
    
    // CPUのターンを処理
    function processCpuTurn() {
        fetch('/api/cpu_turn', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            
            handleGameStateUpdate(data);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('CPUの処理中にエラーが発生しました。');
        });
    }
    
    // ゲーム状態の更新を処理
    function handleGameStateUpdate(data) {
        // ゲーム終了の場合
        if (data.game_over) {
            showResults(data);
            return;
        }
        
        // ゲーム状態を更新
        gameState.currentPlayer = data.current_player;
        gameState.turnCount = data.turn_count;
        gameState.isPlayerTurn = data.is_player_turn;
        gameState.gameLog = data.game_log;
        
        // UI更新
        updateGameLog();
        updateCurrentPlayerInfo();
        
        // CPUのターンなら自動で処理
        if (data.is_cpu_turn) {
            setTimeout(processCpuTurn, 1000);
        }
    }
    
    // 結果表示
    function showResults(data) {
        const resultContent = document.getElementById('result-content');
        resultContent.innerHTML = '';
        
        // 結果ヘッダー
        let resultHTML = '<h4>===== 結果発表 =====</h4><br>';
        
        // 各プレイヤーの結果
        data.players_results.forEach(player => {
            resultHTML += `<strong>${player.name}さんの注文:</strong><br>`;
            
            player.orders.forEach(order => {
                resultHTML += `  - ${order.name}: ${order.price.toLocaleString()}円<br>`;
            });
            
            resultHTML += `  <strong>合計: ${player.total.toLocaleString()}円</strong><br>`;
            resultHTML += `  <strong>目標との差額: ${player.diff.toLocaleString()}円</strong><br><br>`;
        });
        
        // 目標金額
        resultHTML += `<strong>目標金額: ${data.target_price.toLocaleString()}円</strong><br><br>`;
        
        // 勝者と敗者
        resultHTML += `<strong>目標金額に最も近かったのは ${data.winners.join(', ')}さん です！</strong><br><br>`;
        resultHTML += `<strong>目標金額から最も遠かったのは ${data.losers.join(', ')}さん です！</strong><br>`;
        resultHTML += `<strong>${data.losers.join(', ')}さんの支払いとなります！</strong><br><br>`;
        
        // プレイヤーの結果
        if (data.is_player_loser) {
            resultHTML += '<h4>残念！ あなたの支払いです！</h4>';
        } else if (data.is_player_winner) {
            resultHTML += '<h4>おめでとう！ あなたが目標金額に最も近く、勝者です！</h4>';
        } else {
            resultHTML += '<h4>あなたは支払いを免れました！</h4>';
        }
        
        resultContent.innerHTML = resultHTML;
        
        // 結果タブに切り替え
        document.getElementById('result-tab-btn').click();
    }
});
