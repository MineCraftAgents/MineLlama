async function fillBucketWithWater(bot) {
  //地表に移動する
  await moveToGroundLevel(bot);
  
  // Find a water block nearby
  let waterBlocks = bot.findBlocks({
    matching: [mcData.blocksByName.water.id],
    maxDistance: 32,
    count: 1024
  }); 
  if (waterBlocks.length != 0) {
    bot.chat("Found a water block nearby");
  } else {
    bot.chat("No water block found nearby. Exploring...");
    waterBlocks = await exploreUntil(bot, new Vec3(1, 0, 1), 60, () => {
      return bot.findBlocks({
        matching: [mcData.blocksByName.water.id],
        maxDistance: 32,
        count: 1024
      });
    });
    if (waterBlocks.length === 0) {
      bot.chat("Still couldn't find any water block.");
      return; // 水が見つからなければ終了
    }
  }

  //waterBlockの周囲のwaterではないブロックをtargetsに追加
  const targets = [];

  for (let i = 0; i < waterBlocks.length; i++) {
    let adjacentBlock = bot.blockAt((waterBlocks[i]).offset(1, 0, 0)); // xが3ずれる


    if (adjacentBlock.name != 'water') { // adjacentBlockがwater出ない時にtrueとなる条件式
      let position = adjacentBlock.position;

      // Botの位置とadjacentBlockの位置が正しく存在するか確認
      if (bot.entity && bot.entity.position && position) {
        try {
          let distance = bot.entity.position.distanceTo(position); 
          targets.push({ position, distance });
        } catch (error) {
          bot.chat(`距離計算中にエラー: ${error.message}`);
        }
      } else {
        bot.chat("Botの位置またはブロックの位置が無効です");
      }
    }
  }

  if (targets.length > 0) {
    targets.sort((a, b) => a.distance - b.distance);
  }


  // targetに移動
  if (targets.length > 0) {
    await bot.pathfinder.goto(
      new GoalGetToBlock(targets[0].position.x, targets[0].position.y, targets[0].position.z)
    );
  } else {
    bot.chat("No suitable target found near the water block.");
    return;
  }
  bot.chat("targetに移動");

  // Equip the bucket
  const bucket = bot.inventory.findInventoryItem(mcData.itemsByName.bucket.id);
  if (!bucket) {
    bot.chat("you don't have a bucket");
    return;
  }
  await bot.equip(bucket, "hand");

  // Look at the water block
  let waterBlock = bot.findBlock({
      matching: mcData.blocksByName.water.id,
      maxDistance: 2,
    });
  try {
    await bot.lookAt(waterBlock.position);
  } catch (error) {
    bot.chat(`bot.lookAtでエラー: ${error.message}`)
  }
    // Activate the bucket to collect water
  try {
    await bot.activateItem();
  } catch (error) {
    bot.chat(`bot.activateItemでエラー: ${error.message}`)
  }
  bot.chat("Filled the bucket with water.");
  
}
