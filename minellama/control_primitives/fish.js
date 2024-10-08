async function fish(bot, count) {
  const maxTryTime = 30 * 1000; // 最大試行時間を30秒に設定
  const startTime = Date.now();
  
  // 釣り竿をインベントリから探す
  let fishingRod = bot.inventory.findInventoryItem(mcData.itemsByName.fishing_rod.id);
  if (!fishingRod) {
    bot.chat("I don't have a fishing rod");
    return;
  }

  let waterBlocks = null;
  while (!waterBlocks || waterBlocks.length < 10) {
    waterBlocks = bot.findBlocks({
      matching: (block) => block.name === 'water',
      maxDistance: 10, // 探索する最大距離
      count: 30        
    });

    if (waterBlocks.length > 10) {
      break;
    }

    await moveForward(bot, 10);
  }

  bot.chat(`Found water source.`)
  
  let standingPosition = null;
  let waterBlock;
  for (let i = 0; i < waterBlocks.length; i++) {
    const waterBlockPosition = waterBlocks[i];
    waterBlock = bot.blockAt(waterBlockPosition);

    // 隣接するブロックを調べる
    const positionsToCheck = [
      waterBlock.position.offset(1, 0, 0),  // X+1
      waterBlock.position.offset(-1, 0, 0),
      waterBlock.position.offset(1, 1, 0),
      waterBlock.position.offset(-1, 1, 0),
      waterBlock.position.offset(1, 2, 0),
      waterBlock.position.offset(-1, 2, 0), // X-1
      waterBlock.position.offset(0, 0, 1),  // Z+1
      waterBlock.position.offset(0, 0, -1),
      waterBlock.position.offset(0, 1, 1),
      waterBlock.position.offset(0, 1, -1),
      waterBlock.position.offset(0, 2, 1),
      waterBlock.position.offset(0, 2, -1)  // Z-1
    ];

    for (const position of positionsToCheck) {
      const adjacentBlock = bot.blockAt(position);

      // ブロックが水でも空気でもないなら、それは立てる場所
      if (adjacentBlock && adjacentBlock.name !== 'water' && adjacentBlock.name !== 'air') {
        // そのブロックの1つ上のブロックを確認
        const blockAbove = bot.blockAt(position.offset(0, 1, 0));

        // 1つ上のブロックが空気ブロックか確認
        if (blockAbove && blockAbove.name === 'air') {
          bot.chat(`Found standing position. ${adjacentBlock.name}`);
          standingPosition = position; // 立てる場所を保存
          break;
        }
      }
    }

    // 立てる場所が見つかった場合、ループを終了
    if (standingPosition) {
      break;
    }
  }

  // 立てる場所が見つかった場合
  if (standingPosition) {
    await bot.pathfinder.goto(new GoalBlock(standingPosition.x, standingPosition.y, standingPosition.z));
    bot.chat("Standing position found and moved to.");
  } else {
    bot.chat("No suitable standing position found.");
    return;
  }

  // 水ブロックの方向を向く
  await bot.lookAt(waterBlock.position);

  // 釣り竿を装備
  await bot.equip(fishingRod, "hand");

  // 釣りを繰り返すループ
  for (let i = 0; i < count; i++) {
    const elapsedTime = Date.now() - startTime;
    if (elapsedTime >= maxTryTime) {
      bot.chat(`Failed to fish within ${maxTryTime / 1000} seconds.`);
      return;
    }

    try {
      await bot.fish();
      bot.chat(`Fish ${i + 1} caught.`);
    } catch (error) {
      if (error.message === "Fishing cancelled") {
        bot.chat("Fishing was cancelled. Trying again...");
        i--; // 同じ試行を再試行
      } else {
        throw error;
      }
    }
  }
}
