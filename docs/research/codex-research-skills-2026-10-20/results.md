| Skill | Model | Effort | n | Failed | Concepts raw/grounded | Claims raw/accepted | Quality | Precision coverage /24 | Depth /3 | Deep claims | Seconds | Output tokens† |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| dr | gpt-6-luna | medium | 2 | 0 | 7.5/5.5 | 30.0/27.5 | 91.8% | 12.0 | 2.38 | 13.0 | 24 | 2894 |
| dr | gpt-6-luna | max | 2 | 0 | 20.0/13.5 | 35.5/34.0 | 95.7% | 11.0 | 2.34 | 15.0 | 199 | 27570 |
| dr | gpt-6.1-sol | medium | 2 | 0 | 18.5/16.5 | 36.0/33.0 | 91.7% | 9.5 | 2.41 | 15.0 | 76 | 4190 |
| dr | gpt-6.1-sol | max | 2 | 0 | 20.5/17.5 | 36.0/35.0 | 97.2% | 10.5 | 2.37 | 14.0 | 476 | 21876 |
| dr | gpt-6-astra | medium | 2 | 0 | 17.0/15.0 | 36.0/35.5 | 98.6% | 9.0 | 2.42 | 17.0 | 97 | 4290 |
| dr | gpt-6-astra | max | 2 | 0 | 19.0/16.0 | 36.0/35.5 | 98.6% | 10.0 | 2.44 | 16.5 | 660 | 23198 |
| concept-family-explorer | gpt-6-luna | medium | 2 | 0 | 7.0/6.0 | 19.0/18.5 | 97.6% | 9.0 | 2.48 | 9.5 | 23 | 2362 |
| concept-family-explorer | gpt-6-luna | max | 2 | 0 | 12.5/12.5 | 34.0/31.0 | 91.2% | 8.0 | 2.45 | 14.5 | 145 | 19584 |
| concept-family-explorer | gpt-6.1-sol | medium | 2 | 0 | 17.0/17.0 | 34.5/33.5 | 97.2% | 8.5 | 2.43 | 14.5 | 112 | 6199 |
| concept-family-explorer | gpt-6.1-sol | max | 2 | 0 | 18.0/18.0 | 36.0/35.0 | 97.2% | 13.5 | 2.49 | 18.5 | 523 | 25850 |
| concept-family-explorer | gpt-6-astra | medium | 2 | 0 | 15.5/15.5 | 35.5/35.5 | 100.0% | 12.0 | 2.46 | 17.0 | 105 | 4432 |
| concept-family-explorer | gpt-6-astra | max | 2 | 0 | 18.5/18.5 | 36.0/35.0 | 97.2% | 12.0 | 2.48 | 17.5 | 694 | 23360 |
| rabbithole | gpt-6-luna | medium | 2 | 0 | 6.5/5.0 | 25.0/22.0 | 89.2% | 10.5 | 2.50 | 12.5 | 28 | 3362 |
| rabbithole | gpt-6-luna | max | 2 | 0 | 17.0/12.5 | 36.0/34.5 | 95.8% | 11.5 | 2.47 | 18.0 | 218 | 29488 |
| rabbithole | gpt-6.1-sol | medium | 2 | 0 | 18.0/15.0 | 36.0/36.0 | 100.0% | 6.0 | 2.47 | 18.5 | 121 | 5446 |
| rabbithole | gpt-6.1-sol | max | 2 | 0 | 21.0/16.5 | 36.0/36.0 | 100.0% | 11.0 | 2.48 | 18.0 | 632 | 27067 |
| rabbithole | gpt-6-astra | medium | 2 | 0 | 17.0/13.5 | 36.0/35.5 | 98.6% | 7.0 | 2.50 | 19.0 | 117 | 4570 |
| rabbithole | gpt-6-astra | max | 2 | 0 | 17.0/14.5 | 36.0/35.0 | 97.2% | 8.5 | 2.44 | 16.5 | 712 | 25096 |

Values are means across n successful trials. Grounded concepts and accepted atomic claims use one fixed blind Astra/high judge plus deterministic quote matching. Precision coverage requires one accepted claim to state a rubric item adequately. Failed calls have no invented quality scores.

†Reported output tokens include reasoning tokens; they do not measure final-answer length alone. Full usage is in results.json.
