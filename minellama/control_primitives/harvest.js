async function harvest(bot, count) {
    let harvestedCount = 0;
    bot.chat(`Waiting for crops to grow... (Target: ${count})`);

    while (harvestedCount < count) {
        if(!findWheat(bot)){
            bot.chat("No wheat nearby. Please plant seeds first.");
            return;
        }
        const wheatBlock = await waitForGrowth(bot, 1800000);  // 30分

        if (wheatBlock) {
            // 収穫する
            await bot.pathfinder.goto(new GoalBlock(wheatBlock.position.x, wheatBlock.position.y, wheatBlock.position.z));
            const blockToDig = bot.blockAt(wheatBlock.position);
            if (blockToDig) {
                await bot.dig(blockToDig);
                harvestedCount++;
                bot.chat(`Harvest complete. Current count: ${harvestedCount}/${count}`);
            } else {
                bot.chat("Block not found. Retrying...");
            }
        } else {
            bot.chat("Growth wait time ended before harvesting the target count.");
            break;
        }
    }

    bot.chat(`${harvestedCount} wheat harvested.`);
    bot.chat(`Inventory: ${bot.inventory.items().map(item => item.name).join(', ')}`);
}

async function waitForGrowth(bot, timeout) {
    const interval = 60000; // 1分間隔でチェック
    let elapsed = 0;

    bot.chat("Waiting for crops to grow...");

    while (elapsed < timeout) {
        // 周囲のブロックをチェックして、収穫可能な小麦があるか確認
        const wheatBlock = findMatureWheat(bot);
        if (wheatBlock) {
            bot.chat("Harvestable wheat found. Starting to harvest.");
            return wheatBlock; // 収穫可能な小麦が見つかったら返す
        }
        await new Promise(resolve => setTimeout(resolve, interval));
        elapsed += interval;

        bot.chat(`Elapsed time: ${elapsed / 1000} seconds`);
    }

    bot.chat("Growth wait complete.");
    return null; // タイムアウトした場合
}

function findWheat(bot){
    const range = 64;  // ボットの周囲32ブロック以内を探索
    const botPos = bot.entity.position;

    for (let x = -range; x <= range; x++) {
        for (let y = -12; y <= 12; y++) {
            for (let z = -range; z <= range; z++) {
                const position = botPos.offset(x, y, z);
                const block = bot.blockAt(position);

                if (block && block.name === 'wheat') {
                    return true;
                }
            }
        }
    }

    return false; // 収穫可能な小麦が見つからなかった場合
}

function findMatureWheat(bot) {
    const range = 64;  // ボットの周囲32ブロック以内を探索
    const botPos = bot.entity.position;

    for (let x = -range; x <= range; x++) {
        for (let y = -range; y <= range; y++) {
            for (let z = -range; z <= range; z++) {
                const position = botPos.offset(x, y, z);
                const block = bot.blockAt(position);

                if (block && block.name === 'wheat') {
                    const metadata = block.metadata;  // 小麦の成長段階を取得
                    bot.chat(`Wheat growth stage: ${metadata}`);

                    if (metadata === 7) { // 7は小麦の最終段階（収穫可能）
                        bot.chat(`Harvestable wheat found at: ${position}`);
                        return block; // 収穫可能な小麦ブロックを返す
                    }
                }
            }
        }
    }

    return null; // 収穫可能な小麦が見つからなかった場合
}