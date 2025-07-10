async function craftFurnace(bot) {
  const furnaceCount = bot.inventory.count(mcData.itemsByName.furnace.id);
  await craftCraftingTable(bot);
  
  if (furnaceCount >= 1){
    return;
  } else {
    const wd_px_Count = bot.inventory.count(mcData.itemsByName.wooden_pickaxe.id);
    const cobblestoneCount = bot.inventory.count(mcData.itemsByName.cobblestone.id);
    if (wd_px_Count < 1) {
      await mineWoodLog(bot, 3);
      await craftPlanks(bot, 12);
      await craftItem(bot, "stick", 2);
      const craftingTablePosition_px = bot.entity.position.offset(1, 0, 0);
      await placeItem(bot, "crafting_table", craftingTablePosition_px);
      await craftItem(bot, "wooden_pickaxe", 1);
      await mineBlock(bot, "crafting_table", 1);
      bot.chat("Crafted a wooden_pickaxe.");
    }
    if (cobblestoneCount < 8) {
      await mineBlock(bot, "stone", 8 - cobblestoneCount);
      bot.chat("Collected cobblestone.");
    }

    // Place the crafting table near the bot
    const craftingTablePosition = bot.entity.position.offset(1, 0, 0);
    await placeItem(bot, "crafting_table", craftingTablePosition);

    // Craft a furnace using the crafting table
    await craftItem(bot, "furnace", 1);
    bot.chat("Crafted a furnace.");
    return;
  }
}
