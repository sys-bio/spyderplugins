import tecombine as comb

antimonyStr = '''
  S1 -> S2; k1*S1
  S1 = 10; S2 = 0
  k1 = 1
'''

phrasedmlStr = '''
  model1 = model "./simpleuniuni.xml"
  sim1 = simulate uniform(0, 10, 100)
  task1 = run sim1 on model1
  plot time vs S1, S2
'''

comb.export('example.zip', antimonyStr, 'simpleuniuni.xml', phrasedmlStr)