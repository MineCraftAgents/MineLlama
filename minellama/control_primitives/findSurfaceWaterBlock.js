// 地表の水源ブロックを探す関数
function findSurfaceWaterBlock(bot) {
    const range = 32;  // ボットの周囲256ブロック以内を探索
    const botPos = bot.entity.position;
    const yRange = 7;  // ボットの現在のY座標から上下に10ブロックの範囲を探索
    
    let closestWaterBlock = null;
    let closestDistance = Infinity;

    // 水平に探索し、Y軸は上下に2ブロックのみ
    for (let x = -range; x <= range; x++) {
        for (let z = -range; z <= range; z++) {
            for (let yOffset = -yRange; yOffset <= yRange; yOffset++) {
                const position = botPos.offset(x, yOffset, z);
                const block = bot.blockAt(position);

                if (block && block.name === 'water') {
                    const distance = botPos.distanceTo(position);

                    // 最も近い水ブロックを記録
                    if (distance < closestDistance) {
                        closestWaterBlock = block;
                        closestDistance = distance;
                    }
                }
            }
        }
    }

    return closestWaterBlock;
}