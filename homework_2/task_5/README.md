## 1. Как отличаются результаты с:

#### num_beams = 1, length_penalty = 1.0:  
   Фактически то же, что жадный — выбирается всегда самый вероятный токен

#### num_beams = 4, length_penalty = 1.0:  
   Ищет комбинацию с максимальным суммарным лог-пробом. Истории чуть богаче, могут быть длиннее и разнообразнее

#### num_beams = 4, length_penalty = 0.5:  
   Небольшой штраф за длину – относительно поощряются более длинные варианты. История растягивается, добавляются детали

#### num_beams = 4, length_penalty = 2.0:  
   Сильный штраф за длину – предпочтение более коротким ответам. Истории короче, концентрированные

#### num_beams = 8, length_penalty = 1.0:  
   Глубокий обзор больших веток, более качественные сюжетные детали, но риск размазывания внимания

    Однако, в итоге тексты получились все +- одной длины + все тексты вообще почти полностью совпадают
    Из того, что все тексты получились примерно одинаковыми, можно предположить, что lp не сыграл роли из-за большой вероятности получить именно те фразы, которые у меня вышли на разных запусках

## 2. Вопросы
### Помог ли текущий способ исправить проблемы, которые возникли с Greedy Decoding?

Beam search устраняет проблему локальных минимумов greedy: поиск сразу нескольких веток даёт шанс выбрать комбинацию токенов с более высоким общим скором, а не ближайшим локальным максимумом. Истории становятся более связными, реже обрываются или не уходят по странному пути.

### Для какого рода задач beam search подходит больше, чем nucleus sampling?

Beam search детерминированный для фиксированного seed, поэтому хорош для задач, где важна точность и полнота: например, кодогенерация, структурированные ответы.

Nucleus sampling даёт творческое разнообразие, лучше подходит для генерации художественных текстов, когда нужна некоторая рандомность.

## 3. Результат

=== Hedgehog story (beams=1, lp=1.0) ===

Once upon a time, in a small, cozy village nestled in the heart of the forest, there lived a tiny hedgehog named Sonic. Sonic was a curious and adventurous creature, always eager to explore the world around him. One day, while wandering through the forest, Sonic stumbled upon a hidden cave.

Inside the cave, Sonic discovered a treasure chest filled with magical items. As he opened the chest, he was amazed to see that the items were not just ordinary, but enchanted. Sonic was thrilled to find that he could use the items to help others in need.

From that day on, Sonic became a hero in the village. He used his magical powers to help people in need, and soon, the village was filled with people who were grateful for the help they received from Sonic.

Sonic's story became a legend, and people from all over the village would tell stories about him. Sonic's adventures and his magic helped to bring joy and hope to the people of the village, and he was loved and respected by all who knew him.

And so, Sonic continued to be a tiny hedgehog, always on the lookout for new adventures and helping others in need.

=== JSON (beams=1, lp=1.0) ===

{"contractor": "Mike", "sum": 105, "currency": "rubles"}

=== Hedgehog story (beams=4, lp=1.0) ===

Once upon a time, in a small village nestled in the heart of a dense forest, there lived a tiny hedgehog named Sonic. Sonic was a curious and adventurous creature, always eager to explore the world around him. One day, while wandering through the forest, Sonic stumbled upon a hidden cave.

Inside the cave, Sonic discovered a treasure chest filled with strange and magical items. As he opened the chest, he realized that the items were not just ordinary, but were imbued with the power of the forest itself. Sonic knew that he had to find a way to return the treasure back to its rightful owner, the forest itself.

With great courage and determination, Sonic set out on a journey to retrieve the treasure. Along the way, he encountered various challenges and obstacles, but he never gave up. Finally, after a long and grueling journey, Sonic arrived at the forest's heart, where the treasure was hidden.

With the treasure in hand, Sonic returned to the village and presented it to the wise old owl who lived in the forest. The owl, impressed by Sonic's bravery and ingenuity, granted him the power to control the forest's magic. Sonic used his newfound abilities to restore balance to the ecosystem, ensuring that the forest remained healthy and thriving.

From that day on, Sonic became known as the guardian of the forest and its magic. He continued to explore the world around him, always eager to learn and discover new things. And Sonic, the tiny hedgehog, lived happily ever after, forever grateful for the adventure that had brought him to this magical place.

=== JSON (beams=4, lp=1.0) ===

{"contractor": "Mike", "sum": 105, "currency": "RUB"}

=== Hedgehog story (beams=4, lp=0.5) ===

Once upon a time, in a small village nestled in the heart of a dense forest, there lived a tiny hedgehog named Sonic. Sonic was a curious and adventurous creature, always eager to explore the world around him. One day, while wandering through the forest, Sonic stumbled upon a hidden cave.

Inside the cave, Sonic discovered a treasure chest filled with strange and magical items. As he opened the chest, he realized that the items were not just ordinary, but were imbued with the power of the forest itself. Sonic knew that he had to find a way to return the treasure back to its rightful owner, the forest itself.

With great courage and determination, Sonic set out on a journey to retrieve the treasure. Along the way, he encountered various challenges and obstacles, but he never gave up. Finally, after a long and grueling journey, Sonic arrived at the forest's heart, where the treasure was hidden.

With the treasure in hand, Sonic returned to the village and presented it to the wise old owl who lived in the forest. The owl, impressed by Sonic's bravery and ingenuity, granted him the power to control the forest's magic. Sonic used his newfound abilities to restore balance to the ecosystem, ensuring that the forest remained healthy and thriving.

From that day on, Sonic became known as the guardian of the forest and its magic. He continued to explore the world around him, always eager to learn and discover new things. And Sonic, the tiny hedgehog, lived happily ever after, forever grateful for the treasure he had found.


=== JSON (beams=4, lp=0.5) ===

{"contractor": "Mike", "sum": 105, "currency": "RUB"}

=== Hedgehog story (beams=4, lp=2.0) ===

Once upon a time, in a small village nestled in the heart of a dense forest, there lived a tiny hedgehog named Sonic. Sonic was a curious and adventurous creature, always eager to explore the world around him. One day, while wandering through the forest, Sonic stumbled upon a hidden cave.

Inside the cave, Sonic discovered a treasure chest filled with strange and magical items. As he opened the chest, he realized that the items were not just ordinary, but were imbued with the power of the forest itself. Sonic knew that he had to find a way to return the treasure back to its rightful owner, the forest itself.

With great courage and determination, Sonic set out on a journey to retrieve the treasure. Along the way, he encountered various challenges and obstacles, but he never gave up. Finally, after a long and grueling journey, Sonic arrived at the forest's heart, where the treasure was hidden.

With the treasure in hand, Sonic returned to the village and presented it to the wise old owl who lived in the forest. The owl, impressed by Sonic's bravery and ingenuity, granted him the power to control the forest's magic. Sonic used his newfound abilities to restore balance to the ecosystem, ensuring that the forest remained healthy and thriving.

From that day on, Sonic became known as the guardian of the forest and its magic. He continued to explore the world around him, always eager to learn and discover new things. And Sonic, the tiny hedgehog, lived happily ever after in the heart of the forest, forever grateful for the treasure he had found.

=== JSON (beams=4, lp=2.0) ===

{"contractor": "Mike", "sum": 100.5, "currency": "RUB"}

=== Hedgehog story (beams=8, lp=1.0) ===

Once upon a time, in a small village nestled in the heart of a dense forest, there lived a tiny hedgehog named Sonic. Sonic was a curious and adventurous creature, always eager to explore the world around him. One day, as Sonic was wandering through the forest, he stumbled upon a hidden cave.

Inside the cave, Sonic was greeted by a group of friendly creatures who welcomed him with open arms. One of the creatures was a wise old owl named Whiskers. Whiskers explained to Sonic that the cave was home to a group of magical creatures who lived in harmony with nature.

Over the next few days, Sonic spent his days exploring the cave and learning about the creatures who lived there. He discovered that the cave was home to a variety of magical creatures, including pixies, griffins, and unicorns. Each creature had its own unique abilities and powers, and Sonic was fascinated by them all.

As the days turned into weeks, and the weeks turned into months, Sonic's friendship with the magical creatures grew stronger and stronger. He learned to work with them, to communicate with them, and to protect them from any threats that might come their way.

One day, while exploring the cave, Sonic stumbled upon a group of griffins who were attacking a group of pixies. Sonic knew that he had to help the pixies, but he also knew that he had to be careful not to get too close to the griffins.

With the help of Whiskers and the pixies, Sonic managed to defeat the griffins and save the day. The pixies were overjoyed to have their friend back, and Sonic felt a sense of pride and accomplishment that he had never felt before.

From that day on, Sonic became known as a hero among the magical creatures of the cave. He continued to explore the cave and learn more about the world around him, always ready to help those in need. And Sonic, the tiny hedgehog, lived happily ever after, with Whiskers by his side and the magical creatures of the cave by his side.


=== JSON (beams=8, lp=1.0) ===

{"contractor": "Mike", "sum": 105, "currency": "RUB"}