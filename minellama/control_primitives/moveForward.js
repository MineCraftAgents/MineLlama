async function moveForward(bot, distance) {
    const currentPosition = bot.entity.position;
    const forwardVector = bot.entity.yaw; // 現在の向き（yaw）に基づいて前方方向を計算

    // 64ブロック前方の目標位置を計算
    const targetPosition = currentPosition.offset(
        Math.cos(forwardVector) * distance, // x方向
        0,                            // y方向（高さはそのまま）
        Math.sin(forwardVector) * distance  // z方向
    );

    bot.chat("Moving forward...");
    
    // 目標位置に移動
    try {
        // await bot.pathfinder.goto(new GoalNear(targetPosition.x, currentPosition.y, targetPosition.z, 10));
        await bot.pathfinder.goto(new GoalXZ(targetPosition.x, targetPosition.z));
        bot.chat("Arrived at the target position.");
    } catch (err) {
        bot.chat("Failed to move forward: " + err.message);
    }
}