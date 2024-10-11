async function craft(bot, name, count = 1) {
  // items which don't require crafting table
    const maxTryTime = 30 * 1000; // 最大試行時間を30秒に設定
    const startTime = Date.now();
    const withoutCraftingTable = ["crafting_table", "stick"]

    if (name === "planks") {
      await craftPlanks(bot, count);
      return;
    } 
    if (withoutCraftingTable.includes(name)) {
      let itemCount = bot.inventory.count(mcData.itemsByName[name].id);
      while(itemCount < count) {
        await craftItem(bot,name,1);
        itemCount = bot.inventory.count(mcData.itemsByName[name].id);
      }
      return;
    }
    //Place crafting table first
    const suitablePosition = bot.entity.position.offset(1, 0, 0);
    const block = bot.blockAt(suitablePosition);
    if (block.name === "grass_block" || block.name === "dirt") {
      await bot.dig(block);
    }
    await placeItem(bot, "crafting_table", suitablePosition);
    //Craft items with crafting table
    const initialCount = bot.inventory.count(mcData.itemsByName[name].id);
    let itemCount = initialCount;
    while((itemCount - initialCount) < count) {
      const elapsedTime = Date.now() - startTime;
      if (elapsedTime >= maxTryTime) {
          bot.chat(`Failed to craft ${name} within ${maxTryTime / 1000} seconds.`);
          return;
      }
      await craftItem(bot, name, 1);
      itemCount = bot.inventory.count(mcData.itemsByName[name].id);
    }
    bot.chat(`Crafted ${count} ${name}.`);
    //Collect the crafting table
    await mineBlock(bot, "crafting_table", 1);
    bot.chat("Collected a crafting table");
  }