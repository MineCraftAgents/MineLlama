async function mine(bot, name, count, tool=null){
    if (name === "log"){
        await mineWoodLog(bot,count);
        return;
    }

    let blockName;
    const maxTryTime = 90 * 1000; // 最大試行時間を30秒に設定
    const startTime = Date.now();

    if (name === "cobblestone") {
        blockName = "stone";
    } else if (name === "raw_iron") {
        blockName = "iron_ore"
    } else {
        blockName = name;
    }

    const blocksRequiringIronPickaxe = ["gold_ore", "diamond_ore", "emerald_ore", "redstone_ore"];
    if (blockName === "iron_ore") {
        tool = "stone_pickaxe"
    } else if (blocksRequiringIronPickaxe.includes(blockName)) {
        tool = "iron_pickaxe";
    }
    if (tool !== null){
        const equipedTool = bot.inventory.findInventoryItem(mcData.itemsByName[tool].id);
        if(!equipedTool) {
            bot.chat("you don't have a tool")
            return
        }
        await bot.equip(equipedTool, "hand");
    }


    // function getRandomChoice() {
    //     const randomNumber = Math.floor(Math.random() * 3) - 1;
    //     return randomNumber;
    // }

    // Inventoryで個数を確認するようにしていたが、block名とitem名が異なることがあるため、単純に回数をカウントするようにした。
    // let itemCount = bot.inventory.count(mcData.itemsByName[name].id);
    let itemCount = 0;
    while (itemCount < count){
        // let x = getRandomChoice();
        // let y = getRandomChoice();
        // let z = getRandomChoice();
        const elapsedTime = Date.now() - startTime;
        if (elapsedTime >= maxTryTime) {
            bot.chat(`Failed to mine ${name} within ${maxTryTime / 1000} seconds.`);
            return;
        }
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
        // itemCount = bot.inventory.count(mcData.itemsByName[name].id);
        itemCount += 1;
    }

    if (tool !== null){
        await bot.unequip("hand");
    }
}