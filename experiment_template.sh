# タスクリスト
TASK_LIST=('stick' 'crafting_table' 'wooden_pickaxe' 'wooden_shovel' 'wooden_axe' 'wooden_hoe' 'wooden_sword' 'stone_sword' 'stone_shovel' 'stone_pickaxe' 'stone_axe' 'stone_hoe' 'iron_sword' 'iron_shovel' 'iron_pickaxe' 'iron_axe' 'iron_hoe' 'chest' 'furnace' 'glass' 'white_bed' 'boat' 'smoker' 'barrel' 'fence' 'wooden_door' 'campfire' 'bucket' 'ladder' 'shears' 'shield')


# パス設定
SERVER_DIR="/path/to/java_server"
BOT_DIR="/path/to/MineLlama"
WORLD_DIR="$SERVER_DIR/server_name"
LOG_FILE="$SERVER_DIR/server.log"
SCREEN_NAME="screen_name"

for TASK in "${TASK_LIST[@]}"; do
    # 実験は10回繰り返す
    for i in {1..10}; do
        echo "=== タスク開始: $TASK ==="

        #サーバー起動
        echo "Starting Minecraft server..."
        : > "$LOG_FILE"
        screen -S "$SCREEN_NAME" -X stuff "cd $SERVER_DIR && java -Xmx1024M -Xms1024M -jar server.jar nogui > server.log 2>&1\n"

        # サーバーが完全に起動するのを待つ（"Done"が出るまで）
        echo "Waiting for server to fully start (looking for 'Done' in log)..."
        while ! grep -q "Done" "$LOG_FILE"; do
            sleep 2
        done

        # === Bot タスク実行 ===
        echo "Starting bot task..."
        cd "$BOT_DIR"
        python3 server_gpt35_rag.py --task_item "$TASK"

        # === タスク終了後サーバーを停止 ===
        echo "Stopping Minecraft server..."
        screen -S "$SCREEN_NAME" -X stuff "stop\n"

        # サーバーが完全に停止するのを待つ
        sleep 10

        # === ワールド削除 ===
        echo "Deleting world directory..."
        rm -rf "$WORLD_DIR"
        sleep 3

        echo "Task completed and world reset."
    done
done
