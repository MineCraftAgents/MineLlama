async function craftFurnace(bot) {
  const furnaceCount = bot.inventory.count(mcData.itemsByName.furnace.id);
  await craftCraftingTable(bot);
  
  if (furnaceCount >= 1){
    return;
  } else {
    const cobblestoneCount = bot.inventory.count(mcData.itemsByName.cobblestone.id);
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