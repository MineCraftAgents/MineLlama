async function smelt(bot, itemName, count = 1, fuelName = 'planks') {
    // Check and craft furnace first
    await craftFurnace(bot);
    // Check fuel
    let fuel;
    const maxTryTime = 300 * 1000; // 最大試行時間を30秒に設定
    const startTime = Date.now();

    if (fuelName === 'planks') {
      const planksList = ["oak_planks", "birch_planks", "spruce_planks", "jungle_planks", "acacia_planks", "dark_oak_planks", "mangrove_planks"];
      let planksCount = 0;
      for (let key of planksList) {
        planksCount = bot.inventory.count(mcData.itemsByName[key].id);
        if (planksCount > 0) {
          fuel = key;
          break;
        }
      }
      if (fuel === undefined) {
        bot.chat("You don't have any planks.");
        bot.chat("Collecting planks...");
        await mineWoodLog(bot, 1);
        await craftPlanks(bot, 4);
        bot.chat("Planks collected!");
        fuel = 'planks';
        // return;
      }
    } else {
      fuel = fuelName;
    }
    //Place furnace
    const suitablePosition = bot.entity.position.offset(1, 0, 0);
    const block = bot.blockAt(suitablePosition);
    if (block.name === "grass_block" || block.name === "dirt" || block.name === "stone") {
      await bot.dig(block);
    }
    await placeItem(bot, "furnace", suitablePosition);
    //Smelt items with furnace
    let itemCount = 0;
    while(itemCount < count) {
      const elapsedTime = Date.now() - startTime;
      if (elapsedTime >= maxTryTime) {
          bot.chat(`Failed to smelt ${itemName} within ${maxTryTime / 1000} seconds.`);
          return;
      }
      await smeltItem(bot, itemName, fuel, 1);
      itemCount += 1;
    }
    bot.chat(`${count} ${itemName} smelted.`);
    //Collect furnace and item
    await mineBlock(bot, "furnace", 1);
    bot.chat("Collected a furnace");
}