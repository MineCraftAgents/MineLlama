async function showBlock(bot, itemName){
    const item = bot.inventory.findInventoryItem(mcData.itemsByName[itemName].id);
    await bot.equip(item, "hand");
    await bot.chat(`I completed the task and have ${itemName} in my hand now.`)
    await bot.waitForTicks(10);
}