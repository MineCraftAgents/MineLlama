async function craftFishingRod(bot) {
  // Check if we have enough strings
  const maxTryTime = 30 * 1000; // 最大試行時間を30秒に設定
  const startTime = Date.now();
  const requiredStrings = 2;
  const stringsCount = bot.inventory.count(mcData.itemsByName.string.id);
  if (stringsCount < requiredStrings) {
    // Find and kill spiders to obtain strings
    while (bot.inventory.count(mcData.itemsByName.string.id) < requiredStrings) {
      const elapsedTime = Date.now() - startTime;
      if (elapsedTime >= maxTryTime) {
          bot.chat(`Failed to craft fishingrod within ${maxTryTime / 1000} seconds.`);
          return;
      }
      bot.chat("Finding a spider to obtain strings...");
      const spider = await exploreUntil(bot, new Vec3(1, 0, 1), 60, () => {
        const spider = bot.nearestEntity(entity => {
          return entity.name === "spider" && entity.position.distanceTo(bot.entity.position) < 32;
        });
        return spider;
      });
      if (spider) {
        bot.chat("Spider found. Killing it...");
        await killMob(bot, "spider", 300);
        bot.chat("Spider killed.");
      } else {
        bot.chat("Could not find a spider. Trying again...");
      }
    }
  }

  // Place a crafting table if not already placed
  const craftingTable = bot.findBlock({
    matching: mcData.blocksByName.crafting_table.id,
    maxDistance: 32
  });
  if (!craftingTable) {
    const craftingTablePosition = bot.entity.position.offset(1, 0, 0);
    await placeItem(bot, "crafting_table", craftingTablePosition);
    bot.chat("Crafting_table placed.");
  }

  // Craft a fishing rod using the 3 sticks and 2 strings
  await craftItem(bot, "fishing_rod", 1);
  bot.chat("Fishing rod crafted.");
}