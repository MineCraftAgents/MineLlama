async function mine(bot, name, count, tool=null){
    if (name === "log"){
        await mineWoodLog(bot,count);
        return;
    }

    let blockName;
    if (tool !== null){
        const equipedTool = bot.inventory.findInventoryItem(mcData.itemsByName[tool].id);
        await bot.equip(equipedTool, "hand");
    }

    if (name === "cobblestone") {
        blockName = "stone";
    } else if (name === "raw_iron") {
        blockName = "iron_ore"
    } else {
        blockName = name;
    }
    // function getRandomChoice() {
    //     const randomNumber = Math.floor(Math.random() * 3) - 1;
    //     return randomNumber;
    // }

    let itemCount = bot.inventory.count(mcData.itemsByName[name].id);
    while (itemCount < count){
        // let x = getRandomChoice();
        // let y = getRandomChoice();
        // let z = getRandomChoice();
        const targetBlock = await exploreUntil(bot, new Vec3(1, 0, 1), 60, () => {
            const targetBlock = bot.findBlocks({
                matching: mcData.blocksByName[blockName].id,
                maxDistance: 32,
                count:1,
            });
            return targetBlock.length >= 1 ? targetBlock : null;
        });
        if (!targetBlock) {
            bot.chat(`Could not find ${name} : ${mcData.blocksByName[blockName].id}`);
        }
        bot.chat(`This is targetBlock: ${blockName}, ${targetBlock}`);
        await mineBlock(bot, blockName, 1);
        bot.chat(`${targetBlock.length} ${name} mined.`);
        itemCount = bot.inventory.count(mcData.itemsByName[name].id);
    }

    if (tool !== null){
        await bot.unequip("hand");
    }
}