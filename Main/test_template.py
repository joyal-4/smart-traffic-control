from flask import Flask, render_template

app = Flask(__name__)

with app.app_context():
    try:
        result = render_template('enhanced_coordinated_index.html')
        print('✅ Template renders successfully')
        print('📄 Template length:', len(result), 'characters')
        
        # Check for key elements
        if 'Enhanced Coordinated Traffic Control' in result:
            print('✅ Title found')
        if 'coordinator-info' in result:
            print('✅ Coordinator section found')
        if 'switch-progress' in result:
            print('✅ Switch progress found')
        if 'priority-badge' in result:
            print('✅ Priority badges found')
            
    except Exception as e:
        print('❌ Template error:', str(e))
        import traceback
        traceback.print_exc()
