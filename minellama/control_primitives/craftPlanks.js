async function craftPlanks(bot, count=1) {
    //Craft planks from any type of log
    const woodLogNames = {"oak_log":"oak_planks", "birch_log":"birch_planks", "spruce_log":"spruce_planks", "jungle_log":"jungle_planks", "acacia_log":"acacia_planks", "dark_oak_log":"dark_oak_planks", "mangrove_log":"mangrove_planks"};
    let keysList = Object.keys(woodLogNames);
    let craftedCount = 0;

    //If you have a certain type of log, then craft planks from that log until you get enough.
    for (let key of keysList) {
        if (craftedCount >= count) {
            return;
        }
        while(craftedCount < count){
            let woodLogCount = bot.inventory.count(mcData.itemsByName[key].id);
            if (woodLogCount > 0){
                await craftItem(bot, woodLogNames[key], 1);
                craftedCount += 4;
            } else {
                break;
            }
        }
    }
}
