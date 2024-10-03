async function catchFishWithBucket(bot) {
    // バケツを装備
    const bucket = bot.inventory.findInventoryItem(mcData.itemsByName['bucket'].id);
    if (!bucket) {
        bot.chat("I don't have a bucket.");
        return;
    }
    await bot.equip(bucket, 'hand');

    let fish = null;
    let waterBlock = null;
    while (!fish) {
        // 周囲に地表の水源を探す
        while (!waterBlock) {
            waterBlock = findSurfaceWaterBlock(bot);
            bot.chat("No surface water found nearby.");
            // return;
            await moveForward(bot, 32);
        }

        bot.chat("Water source found. Heading to the water source.");

        // 水源の5マス以内に入るまで移動
        await bot.pathfinder.goto(new GoalNear(waterBlock.position.x, waterBlock.position.y, waterBlock.position.z, 10));
        bot.chat("Arrived near the water source.");

        // 魚を探す
        fish = bot.nearestEntity(entity => {
            return entity.name === 'cod' || entity.name === 'salmon' || entity.name === 'tropical_fish' || entity.name === 'pufferfish';
        });

        if (!fish) {
            bot.chat("No fish found nearby.");
        }
    }

    bot.chat("Found fish.")
    // 魚に近づく
    await bot.pathfinder.goto(new GoalBlock(fish.position.x, fish.position.y, fish.position.z));

    // 魚をすくう
    try {
        await bot.activateEntity(fish);
        bot.chat("Got the fish with the bucket!");
    } catch (err) {
        bot.chat(`Failed to catch the fish: ${err.message}`);
    }
}
