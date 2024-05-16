async function craftCraftingTable(bot){
    const craftingTableCount = bot.inventory.count(mcData.itemsByName.crafting_table.id);
    if (craftingTableCount >= 1){
      return;
    } else {
      const planksList = ["oak_planks", "birch_planks", "spruce_planks", "jungle_planks", "acacia_planks", "dark_oak_planks", "mangrove_planks"];
      let planksCount = 0;
      for (let key of planksList) {
        planksCount += bot.inventory.count(mcData.itemsByName[key].id);
      }
      if (planksCount < 4) {
        const logList = ["oak_log", "birch_log", "spruce_log", "jungle_log", "acacia_log", "dark_oak_log", "mangrove_log"];
        let logsCount = 0;
        for (let key of logList) {
          logsCount += bot.inventory.count(mcData.itemsByName[key].id);
        }
        if (logsCount < 1) {
          await mineWoodLog(bot,1);
        }
        await craftPlanks(bot, 4);
        bot.chat("Crafted oak planks.");
      }
      await craftItem(bot, "crafting_table", 1);
      bot.chat("Crafted a crafting table.");
      return;
    }
}