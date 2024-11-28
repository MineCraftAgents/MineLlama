async function placeItem(bot, name, position) {
    // 引数のバリデーション
    if (typeof name !== "string") {
        throw new Error(`name for placeItem must be a string`);
    }
    if (!(position instanceof Vec3)) {
        throw new Error(`position for placeItem must be a Vec3`);
    }

    const itemByName = mcData.itemsByName[name];
    if (!itemByName) {
        throw new Error(`No item named ${name}`);
    }

    const item = bot.inventory.findInventoryItem(itemByName.id);
    if (!item) {
        bot.chat(`No ${name} in inventory`);
        return;
    }

    let _placeItemFailCount = 0;
    const maxRetries = 10;  // リトライの上限

    while (_placeItemFailCount <= maxRetries) {
        // positionがブロックを置けるかどうかを事前にチェック
        if (!isPlaceable(bot, position)) {
            bot.chat(`Initial position is not suitable for placing ${name}. Searching for a new location...`);
            // 置ける場所を探す
            position = await findPlaceableLocation(bot, bot.entity.position, 5);  // 探索範囲を5ブロックに設定
            if (!position) {
                bot.chat(`No suitable location found for placing ${name}.`);
                return;
            }
        }

        const faceVectors = [
            new Vec3(0, 1, 0),
            new Vec3(0, -1, 0),
            new Vec3(1, 0, 0),
            new Vec3(-1, 0, 0),
            new Vec3(0, 0, 1),
            new Vec3(0, 0, -1),
        ];

        let referenceBlock = null;
        let faceVector = null;

        // 置くための基準ブロックを探す
        for (const vector of faceVectors) {
            const block = bot.blockAt(position.minus(vector));
            if (block?.name !== "air") {
                referenceBlock = block;
                faceVector = vector;
                bot.chat(`Placing ${name} on ${block.name} at ${block.position}`);
                break;
            }
        }

        if (!referenceBlock) {
            // 置ける基準ブロックがない場合、移動や掘削を試みてから再探索
            bot.chat(`No block to place ${name} on. Attempting to adjust position.`);
            await moveRandomlyOrDig(bot);
            _placeItemFailCount++;

            // 移動後に再び位置が置けるか確認して再探索
            position = await findPlaceableLocation(bot, bot.entity.position, 5);  // 探索範囲5ブロック
            if (!position) {
                bot.chat(`No suitable location found after moving. Retry ${_placeItemFailCount}/${maxRetries}`);
                continue;  // 新しい位置が見つからない場合はリトライ
            }
        } else {
            // 置ける位置が見つかった場合
            try {
                await bot.pathfinder.goto(new GoalPlaceBlock(position, bot.world, {}));
                await bot.equip(item, "hand");
                await bot.placeBlock(referenceBlock, faceVector);
                bot.chat(`Placed ${name} successfully.`);
                bot.save(`${name}_placed`);
                return; // 成功したので終了
            } catch (err) {
                bot.chat(`Error placing ${name}: ${err.message}. Retrying...`);
                _placeItemFailCount++;

                if (_placeItemFailCount > maxRetries) {
                    throw new Error(`placeItem failed too many times, could not place ${name} after retries.`);
                }

                // 掘削後、もう一度探索して再試行
                await moveRandomlyOrDig(bot);
                position = await findPlaceableLocation(bot, bot.entity.position, 5);  // 再探索
                if (!position) {
                    bot.chat(`No suitable location found after moving. Retry ${_placeItemFailCount}/${maxRetries}`);
                    continue;
                }
            }
        }
    }
}

// 位置が置ける場所かどうかを判定する関数
function isPlaceable(bot, position) {
    const blockAbove = bot.blockAt(position);  // ブロックA（置こうとする場所）
    const blockBelow = bot.blockAt(position.offset(0, -1, 0));  // ブロックB（Aの下のブロック）

    // Aは空気または水で、Bが空気でないブロックならOK
    return blockAbove && blockAbove.name === 'air' && blockBelow && blockBelow.name !== 'air';
}

// 近くに置ける場所を探す関数
async function findPlaceableLocation(bot, startPosition, range = 5) {
    const Vec3 = require('vec3').Vec3;

    // 探索範囲内で置ける場所を探す
    for (let x = -range; x <= range; x++) {
        for (let y = -range; y <= range; y++) {
            for (let z = -range; z <= range; z++) {
                const checkPosition = startPosition.offset(x, y, z);
                if (isPlaceable(bot, checkPosition)) {
                    return checkPosition;
                }
            }
        }
    }
    return null;  // 見つからなかった場合
}

async function moveRandomlyOrDig(bot) {
    const randomOffset = () => (Math.random() > 0.5 ? 1 : -1);

    // ランダムに移動する新しい位置を計算
    const newPosition = bot.entity.position.offset(randomOffset(), 0, randomOffset());
    bot.chat(`Moving to new position at ${newPosition}.`);
    await bot.pathfinder.goto(new GoalNear(newPosition, 1));

    // 周囲のブロックを掘る。足元ではなく、周囲1ブロックの位置を掘削対象にする。
    const digPositions = [
        bot.entity.position.offset(1, 0, 0),
        bot.entity.position.offset(-1, 0, 0),
        bot.entity.position.offset(0, 0, 1),
        bot.entity.position.offset(0, 0, -1),
    ];

    for (const digPosition of digPositions) {
        const block = bot.blockAt(digPosition);
        if (block && block.name !== 'air') {
            bot.chat(`Dug the block at ${digPosition} (${block.name}).`);
            await bot.dig(block);
            break;  // 1つ掘ったら終了
        }
    }
}
