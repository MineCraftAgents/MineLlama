async function harvest(bot, itemName = "wheat", count = 1) {
    let harvestedCount = 0;
    bot.chat(`Waiting for crops to grow... (Target: ${count} ${itemName})`);

    while (harvestedCount < count) {
        if (!findCrop(bot, itemName)) {
            bot.chat(`No ${itemName} nearby. Please plant seeds first.`);
            return;
        }
        const cropBlock = await waitForGrowth(bot, itemName, 1800000);  // 30分

        if (cropBlock) {
            // 収穫する
            await bot.pathfinder.goto(new GoalBlock(cropBlock.position.x, cropBlock.position.y, cropBlock.position.z));
            const blockToDig = bot.blockAt(cropBlock.position);
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

    bot.chat(`${harvestedCount} ${itemName} harvested.`);
    bot.chat(`Inventory: ${bot.inventory.items().map(item => item.name).join(', ')}`);
}

async function waitForGrowth(bot, itemName, timeout) {
    const interval = 60000; // 1分間隔でチェック
    let elapsed = 0;

    bot.chat(`Waiting for ${itemName} to grow...`);

    while (elapsed < timeout) {
        // 周囲のブロックをチェックして、収穫可能な作物があるか確認
        const matureCropBlock = findMatureCrop(bot, itemName);
        if (matureCropBlock) {
            bot.chat(`Harvestable ${itemName} found. Starting to harvest.`);
            return matureCropBlock; // 収穫可能な作物が見つかったら返す
        }
        await new Promise(resolve => setTimeout(resolve, interval));
        elapsed += interval;

        bot.chat(`Elapsed time: ${elapsed / 1000} seconds`);
    }

    bot.chat("Growth wait complete.");
    return null; // タイムアウトした場合
}

function findCrop(bot, itemName) {
    const range = 64;  // ボットの周囲32ブロック以内を探索
    const botPos = bot.entity.position;

    for (let x = -range; x <= range; x++) {
        for (let y = -12; y <= 12; y++) {
            for (let z = -range; z <= range; z++) {
                const position = botPos.offset(x, y, z);
                const block = bot.blockAt(position);

                if (block && block.name === itemName) {
                    return true;
                }
            }
        }
    }

    return false; // 収穫可能な作物が見つからなかった場合
}

function findMatureCrop(bot, itemName) {
    const range = 64;  // ボットの周囲32ブロック以内を探索
    const botPos = bot.entity.position;

    for (let x = -range; x <= range; x++) {
        for (let y = -range; y <= range; y++) {
            for (let z = -range; z <= range; z++) {
                const position = botPos.offset(x, y, z);
                const block = bot.blockAt(position);

                if (block && block.name === itemName) {
                    const metadata = block.metadata;  // 作物の成長段階を取得
                    bot.chat(`${itemName} growth stage: ${metadata}`);

                    if (metadata === 7) { // 7は作物の最終段階（収穫可能）
                        bot.chat(`Harvestable ${itemName} found at: ${position}`);
                        return block; // 収穫可能な作物ブロックを返す
                    }
                }
            }
        }
    }

    return null; // 収穫可能な作物が見つからなかった場合
}