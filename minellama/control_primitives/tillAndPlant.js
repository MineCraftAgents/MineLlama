async function tillAndPlant(bot, seedName="wheat_seeds", count=1, hoeName="wooden_hoe") {
    // const hoeName = "wooden_hoe";
    // const seedName = "wheat_seeds";
    const maxAttempts = 3;  // 耕す再試行の最大回数
    const searchRadius = 12;  // ブロックを探す範囲
    const waterProximityRadius = 5;  // 水源の5マス以内で探索を開始

    // bot.chat("/give @s wooden_hoe");
    // bot.chat(`/give @s ${seedName} ${count}`);
    // bot.chat(`/give @s dirt 64`);
    

    await new Promise(resolve => setTimeout(resolve, 2000));

    const hoe = bot.inventory.items().find(item => item.name === hoeName);
    const seeds = bot.inventory.items().find(item => item.name === seedName);
    const dirt = bot.inventory.items().find(item => item.name === "dirt");

    if (!hoe) {
        bot.chat(`Required items are missing: ${hoeName}`);
        return;
    } 
    if (!seeds){
        bot.chat(`Required items are missing: ${seedName}`);
        return;
    }
    
    // 周囲に地表の水源を探す
    let waterBlock = null;
    while (!waterBlock) {
        waterBlock = findSurfaceWaterBlock(bot);
        bot.chat("No surface water found nearby.");
        // return;
        await moveForward(bot, 64);
    }
    
    bot.chat("Water source found. Heading to the water source.");
    
    // 水源の5マス以内に入るまで移動
    await bot.pathfinder.goto(new GoalNear(waterBlock.position.x, waterBlock.position.y, waterBlock.position.z, waterProximityRadius));
    bot.chat("Arrived near the water source.");
    
    let plantedCount = 0;
    
    while (plantedCount < count) {
        // 周囲12マス以内の耕作可能な土ブロックまたは地表ブロックを探す
        let blockPosition = findNearestBlock(bot, searchRadius, true);
        if (!blockPosition) {
            bot.chat("No tillable block found.");
            blockPosition = findNearestBlock(bot, searchRadius, false);
        }
    
        try {
            await bot.pathfinder.goto(new GoalNear(blockPosition.x, blockPosition.y, blockPosition.z, 2));
    
            // 土ブロックをチェックまたは置き換え
            const block = bot.blockAt(blockPosition);
            if (block) {
                bot.chat(`Checking block: ${block.name} at ${blockPosition}`);
    
                if (!isTillable(block)) {
                    bot.chat("Digging the block and replacing it with soil.");
                    let dirtCount = bot.inventory.items().find(item => item.name === "dirt");
                    if (!dirtCount) {
                        await mine(bot, "dirt", 3);
                    }
                    await bot.dig(block);  // ブロックを掘る
                    await bot.equip(dirt, 'hand');
                    await bot.placeBlock(bot.blockAt(blockPosition), new Vec3(0, 1, 0));  // 土ブロックを置く
                }
            }
    
            // 土ブロックを耕す
            const tilledBlock = bot.blockAt(blockPosition);
            if (tilledBlock && isTillable(tilledBlock)) {
                bot.chat("Tilling the soil.");
                await bot.equip(hoe, 'hand');
    
                let success = false;
                for (let attempt = 1; attempt <= maxAttempts; attempt++) {
                    try {
                        await bot.lookAt(tilledBlock.position, true);
                        await bot.activateBlock(tilledBlock);  // これで耕す
    
                        bot.chat(`Tilling complete (Attempt: ${attempt}).`);
    
                        // 実際に耕されたか確認
                        const finalBlock = bot.blockAt(blockPosition);
                        if (finalBlock && finalBlock.name === 'farmland') {
                            bot.chat("Successfully tilled.");
                            success = true;
                            break;
                        } else {
                            bot.chat("Tilling failed, block hasn't changed.");
                        }
                    } catch (err) {
                        bot.chat(`Tilling failed (Attempt: ${attempt}): ${err.message}`);
                    }
                }
    
                if (!success) {
                    bot.chat("Reached maximum attempts, tilling failed. Retrying on the next block.");
                    continue;  // 次のブロックで再試行
                }
    
                // 種を植える
                try {
                    await bot.equip(seeds, 'hand');
                    await bot.placeBlock(bot.blockAt(blockPosition), new Vec3(0, 1, 0));
                    bot.chat("Seeds planted.");
                    plantedCount++;
                } catch (err) {
                    bot.chat("Failed to plant seeds: " + err.message);
                    continue;  // 次のブロックで再試行
                }
            } else {
                bot.chat("The selected block is not tillable. Retrying on the next block.");
            }
    
            // 耕す時間を待つ
            await new Promise(resolve => setTimeout(resolve, 1000));
    
        } catch (err) {
            bot.chat("An error occurred: " + err.message + " Trying another block.");
            return;
        }
    }
    
    bot.chat(`Result: ${plantedCount} ${seedName} planted in total.`);
}

// 周囲の耕作可能な土ブロックまたは地表のブロックを探す関数（最も近いものを返す）
function findNearestBlock(bot, range, onlyTillable) {
    const botPos = bot.entity.position;
    const candidates = [];

    for (let y = -2; y <= 2; y++) {  // Y座標を中心に上下2ブロック範囲
        for (let x = -range; x <= range; x++) {
            for (let z = -range; z <= range; z++) {
                const position = botPos.offset(x, y, z);
                const block = bot.blockAt(position);
                const blockAbove = bot.blockAt(position.offset(0, 1, 0));

                // 耕作可能な場所または地表のブロックを探す
                if (block && block.name !== 'air' && block.name !== "water" && block.name !== "farmland" && blockAbove && blockAbove.name === 'air') {
                    if (onlyTillable && !isTillable(block)) continue;  // 耕作可能なブロックのみを探す場合
                    // その場所が4マス以内に水があるかを確認
                    if (isWaterNearby(bot, position, 4)) {
                        const distance = botPos.distanceTo(position);
                        candidates.push({ position, distance });
                    }
                }
            }
        }
    }

    if (candidates.length > 0) {
        // 最も近いブロックを選ぶ
        candidates.sort((a, b) => a.distance - b.distance);
        return candidates[0].position;
    }

    return null;  // 適切な場所が見つからない場合
}

// 指定されたブロックが耕作可能かを確認する関数
function isTillable(block) {
    return block.name === 'dirt' || block.name === 'grass_block';
}

// 指定された位置の周囲に水があるかを確認する関数
function isWaterNearby(bot, position, radius) {
    for (let x = -radius; x <= radius; x++) {
        for (let z = -radius; z <= radius; z++) {
            const offsetPosition = position.offset(x, 0, z);
            const block = bot.blockAt(offsetPosition);

            if (block && block.name === 'water') {
                return true;
            }
        }
    }
    return false;
}


