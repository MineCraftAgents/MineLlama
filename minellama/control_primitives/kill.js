async function kill(bot, name, count, tool=null){
    if (tool !== null){
        const equipedTool = bot.inventory.findInventoryItem(mcData.itemsByName[tool].id);
        await bot.equip(equipedTool, "hand");
    }

    let killedCount = 0;
    const maxTryTime = 90 * 1000 * count; 
    const startTime = Date.now();

    while (killedCount < count){
        const elapsedTime = Date.now() - startTime;
        if (elapsedTime >= maxTryTime) {
            bot.chat(`Failed to kill ${name} within ${maxTryTime / 1000} seconds.`);
            return;
        }
        const targetEntity = await exploreUntil(bot, new Vec3(1, 0, 1), 60, () => {
            const targetEntity = bot.nearestEntity(entity => {
              return entity.name === name && entity.position.distanceTo(bot.entity.position) < 32;
            });
            return targetEntity;
          });
          if (!targetEntity) {
            bot.chat(`Could not find ${name}.`);
            return;
          }
        
          await killMob(bot, name, 300);
          bot.chat(`Killed ${name}.`);
        
          await bot.pathfinder.goto(new GoalBlock(targetEntity.position.x, targetEntity.position.y, targetEntity.position.z));
          bot.chat("Collected dropped items.");

          killedCount += 1;
    }
    bot.chat(`Result: I killed ${killedCount} ${name} in total.`);
}