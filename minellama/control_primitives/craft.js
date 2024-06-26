async function craft(bot, name, count = 1) {
  // items which don't require crafting table
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
    let itemCount = bot.inventory.count(mcData.itemsByName[name].id);
    while(itemCount < count) {
      await craftItem(bot, name, 1);
      itemCount = bot.inventory.count(mcData.itemsByName[name].id);
    }
    bot.chat(`Crafted ${count} ${name}.`);
    //Collect the crafting table
    await mineBlock(bot, "crafting_table", 1);
  }