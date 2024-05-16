async function moveRandomly(bot) {
    const positions = [
        new Vec3(1, 0, 0),
        new Vec3(-1, 0, 0),
        new Vec3(0, 0, 1),
        new Vec3(0, 0, -1),
        new Vec3(0, 1, 0) // Check above the bot as well
    ];
    
    for (const pos of positions) {
        const block = bot.blockAt(bot.entity.position.plus(pos));
        if (block && bot.canDigBlock(block)) {
        await bot.dig(block);
        }
    }

    const randomDirection = new Vec3((Math.random() - 0.5) * 2, 0, (Math.random() - 0.5) * 2);
    const newPosition = bot.entity.position.plus(randomDirection);
    bot.pathfinder.setGoal(new GoalNear(newPosition.x, newPosition.y, newPosition.z));
    bot.chat("Moved randomly.")
}