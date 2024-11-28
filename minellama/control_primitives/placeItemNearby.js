async function placeItemNearby(bot, name, count) {
    // 引数のバリデーション
    if (typeof name !== "string") {
        throw new Error(`name must be a string`);
    }
    if (typeof count !== "number" || count <= 0) {
        throw new Error(`count must be a positive number`);
    }

    const Vec3 = require('vec3').Vec3;  // Vec3が必要な場合
    const itemByName = mcData.itemsByName[name];
    if (!itemByName) {
        throw new Error(`No item named ${name}`);
    }

    const item = bot.inventory.findInventoryItem(itemByName.id);
    if (!item || item.count < count) {
        bot.chat(`Not enough ${name} in inventory. Required: ${count}`);
        return;
    }

    const range = 5;  // 探索する範囲
    let targetPosition = null;

    // 周囲のブロックを探索して適切な配置場所を探す
    for (let x = -range; x <= range; x++) {
        for (let y = -range; y <= range; y++) {
            for (let z = -range; z <= range; z++) {
                const position = bot.entity.position.offset(x, y, z);
                const blockAbove = bot.blockAt(position);
                const blockBelow = bot.blockAt(position.offset(0, -1, 0));

                // 置く場所は空気であり、下のブロックが空気でないことが条件
                if (blockAbove && blockAbove.name === 'air' && blockBelow && blockBelow.name !== 'air') {
                    targetPosition = position;
                    break;
                }
            }
            if (targetPosition) break;
        }
        if (targetPosition) break;
    }

    if (!targetPosition) {
        bot.chat("No suitable block to place found nearby.");
        return;
    }

    // 見つけた位置にブロックを置く
    try {
        await bot.pathfinder.goto(new GoalBlock(targetPosition.x, targetPosition.y, targetPosition.z));  // 目的の位置に移動
        const referenceBlock = bot.blockAt(targetPosition.offset(0, -1, 0));
        await bot.equip(item, "hand");
        await bot.placeBlock(referenceBlock, new Vec3(0, 1, 0));  // ブロックを置く
        bot.chat(`Placed ${name} at ${targetPosition}`);
        bot.save(`${name}_placed`);

        // 複数のブロックを置く場合、再帰的に呼び出す
        if (count > 1) {
            await placeNearbyItem(bot, name, count - 1);
        }

    } catch (err) {
        bot.chat(`Error placing ${name}: ${err.message}`);
    }
}